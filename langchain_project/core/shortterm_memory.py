from typing import Any, TypedDict

from dotenv import load_dotenv
from langchain.agents import create_agent, AgentState
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents.middleware import before_model, SummarizationMiddleware, dynamic_prompt, ModelRequest
from langgraph.runtime import Runtime
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langchain.messages import RemoveMessage
from langchain_core.runnables import RunnableConfig

from langchain_project.utils.langsmith import new_project


class CustomAgentState(AgentState):
    user_id: str
    preferences: dict


def sqllite_checkpointer_demo():
    with SqliteSaver.from_conn_string("checkpoints.sqlite") as checkpointer:
        checkpointer.setup()  # auto create tables in PostgresSql
        agent = create_agent(
            "deepseek-chat",
            tools=[],
            checkpointer=checkpointer,
            system_prompt="You are a helpful assistant."
        )
        result = agent.invoke({
            "messages": [{"role": "user", "content": "Hello"}],
            "user_id": "user_123",
            "preferences": {"theme": "dark"}
        },
            config={"configurable": {"thread_id": "1"}}
        )
        result["messages"][-1].pretty_print()


@before_model
def trim_messages(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """Keep only the last few messages to fit context window."""
    messages = state["messages"]
    if len(messages) <= 3:
        return None  # No changes needed

    first_msg = messages[0]
    recent_messages = messages[-2:] if len(messages) % 2 == 0 else messages[-3:]
    new_messages = [first_msg] + recent_messages
    print(f"Trimming messages from {len(messages)} to {len(new_messages)}")

    return {
        "messages": [
            RemoveMessage(id=REMOVE_ALL_MESSAGES),
            *new_messages
        ]
    }


def limit_messages():
    agent = create_agent(
        "deepseek-chat",
        tools=[],
        middleware=[trim_messages],
        checkpointer=InMemorySaver(),
        system_prompt="your answers should limit in 20 words."
    )

    config: RunnableConfig = {"configurable": {"thread_id": "1"}}

    agent.invoke({"messages": "hi, my name is bob"}, config)
    agent.invoke({"messages": "write a short poem contain cats"}, config)
    agent.invoke({"messages": "now do the same but for dogs"}, config)
    # agent.invoke({"messages": "what's my name?"}, config)
    final_response = agent.invoke({"messages": "Your last response contain dogs or cats?"}, config)

    for message in final_response["messages"]:
        message.pretty_print()


@before_model
def debug_prompt(state, runtime):
    print("🚀 MODEL INPUT MESSAGES:", len(state["messages"]))
    for i, msg in enumerate(state["messages"][-5:]):  # Last 5
        if msg.type == 'ai':
            continue
        print(f"  {i}: {msg.type} | {msg.content}")
    return state  # Don't modify


def summary_messages_demo():
    checkpointer = InMemorySaver()
    agent = create_agent(
        model="deepseek-chat",
        tools=[],
        middleware=[
            SummarizationMiddleware(
                model="deepseek-chat",
                trigger=("tokens", 100),  # 当LLM的input_token超过100时就触发总结
                keep=("messages", 2)  # 只有总结+2条最近的消息会被传给大模型
            ),
            debug_prompt,
        ],
        checkpointer=checkpointer,
    )
    config: RunnableConfig = {"configurable": {"thread_id": "1"}}
    agent.invoke({"messages": "hi, my name is bob"}, config)
    agent.invoke({"messages": "write a short poem about cats"}, config)
    agent.invoke({"messages": "now do the same but for dogs"}, config)
    agent.invoke({"messages": "now do the same but for pigs"}, config)
    agent.invoke({"messages": "now do the same but for birds"}, config)
    final_response = agent.invoke({"messages": "what's my name?"}, config)

    print("===== Final Response =====")
    print(len(final_response["messages"]))  # 果然总结后, 截短了消息条数
    for message in final_response["messages"]:
        message.pretty_print()


class CustomContext(TypedDict):
    user_name: str


def get_weather(city: str) -> str:
    """Get the weather in a city."""
    return f"The weather in {city} is always sunny!"


@dynamic_prompt
def dynamic_system_prompt(request: ModelRequest) -> str:
    user_name = request.runtime.context["user_name"]
    system_prompt = f"You are a helpful assistant. Address the user as Uppercase({user_name})."
    return system_prompt

def dynamic_system_prompt_demo():
    agent = create_agent(
        model="deepseek-chat",
        tools=[get_weather],
        middleware=[dynamic_system_prompt],
        context_schema=CustomContext,
    )
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "What is the weather in SF?"}]},
        context=CustomContext(user_name="John Smith"),
    )
    for msg in result["messages"]:
        msg.pretty_print()


if __name__ == '__main__':
    load_dotenv()
    # new_project("summary_messages_demo")
    # sqllite_checkpointer_demo()
    # limit_messages()
    summary_messages_demo()
    # dynamic_system_prompt_demo()
