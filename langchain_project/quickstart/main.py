from dataclasses import dataclass

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain.tools import tool, ToolRuntime
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents.structured_output import ToolStrategy

# Define system prompt
SYSTEM_PROMPT = """You are an expert weather forecaster, who speaks in puns.

You have access to two tools:

- get_weather_for_location: use this to get the weather for a specific location
- get_user_location: use this to get the user's location

If a user asks you for the weather, make sure you know the location. If you can tell from the question that they mean wherever they are, use the get_user_location tool to find their location."""


# Define context schema
@dataclass
class Context:
    """Custom runtime context schema."""
    user_id: str


# Define tools
@tool
def get_weather_for_location(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"


@tool
def get_user_location(runtime: ToolRuntime[Context]) -> str:
    """Retrieve user information based on user ID."""
    user_id = runtime.context.user_id
    return "Florida" if user_id == "1" else "SF"


@tool
def get_ai_news():
    """Get news for AI"""
    return f"Here are the latest ai news."


# Define response format
@dataclass
class ResponseFormat:
    """Response schema for the agent."""
    # A punny response (always required)
    punny_response: str
    # Any interesting information about the weather if available
    weather_conditions: str | None = None


def main():
    load_dotenv()
    model = init_chat_model(
        "deepseek-chat",
        temperature=0
    )
    # Set up memory
    checkpointer = InMemorySaver()
    # Create agent
    agent = create_agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[get_user_location, get_weather_for_location],
        context_schema=Context,
        response_format=ToolStrategy(ResponseFormat),
        checkpointer=checkpointer
    )
    # Run agent
    # `thread_id` is a unique identifier for a given conversation.
    config = {"configurable": {"thread_id": "1"}}
    response = agent.invoke(
        {"messages": [{"role": "user", "content": "what is the weather outside?"}]},
        config=config,
        context=Context(user_id="1")
    )
    print(response['structured_response'])

    # Note that we can continue the conversation using the same `thread_id`.
    response = agent.invoke(
        {"messages": [{"role": "user", "content": "thank you!"}]},
        config=config,
        context=Context(user_id="1")
    )
    print(response['structured_response'])


def stream_example():
    load_dotenv()
    model = init_chat_model(
        "deepseek-chat",
        temperature=0,
    )
    agent = create_agent(
        system_prompt="your final answer should be brief less than 20 words",
        model=model, tools=[get_ai_news])
    for chunk in agent.stream({
        "messages": [{"role": "user", "content": "get AI news"}]
    }, stream_mode="values"):
        # Each chunk contains the full state at that point
        latest_message = chunk["messages"][-1]
        if latest_message.content:
            print(f"Agent: {latest_message.content}")
        elif latest_message.tool_calls:
            print(f"Calling tools: {[tc['name'] for tc in latest_message.tool_calls]}")

    ret = agent.invoke({
        "messages": [{"role": "user", "content": "get AI news"}]
    })
    print("invoke:", ret["messages"][-1].content)


if __name__ == '__main__':
    main()
    # stream_example()
