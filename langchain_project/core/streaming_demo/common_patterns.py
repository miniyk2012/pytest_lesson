from typing import Any, Literal

from dotenv import load_dotenv
from langchain.agents import create_agent
from langgraph.config import get_stream_writer
from pydantic import BaseModel
from langgraph.runtime import Runtime
from langchain.chat_models import init_chat_model

from langchain.agents.middleware import after_agent, AgentState
from langchain.messages import AIMessage, AIMessageChunk, AnyMessage, ToolMessage


def get_weather(city: str) -> str:
    """Get weather for a given city."""

    return f"It's always sunny in {city}!"


def _render_message_chunk(token: AIMessageChunk) -> None:
    if token.text:
        print(token.text, end="|")
    if token.tool_call_chunks:
        print(token.tool_call_chunks)
    # N.B. all content is available through token.content_blocks


def _render_completed_message(message: AnyMessage) -> None:
    if isinstance(message, AIMessage) and message.tool_calls:
        print(f"Tool calls: {message.tool_calls}")
    if isinstance(message, ToolMessage):
        print(f"Tool response: {message.content_blocks}")


def stream_tool_calls(agent):
    input_message = {"role": "user", "content": "What is the weather in Boston?"}
    for stream_mode, data in agent.stream(
            {"messages": [input_message]},
            stream_mode=["messages", "updates"],
    ):
        if stream_mode == "messages":
            token, metadata = data
            if isinstance(token, AIMessageChunk):
                _render_message_chunk(token)
        if stream_mode == "updates":
            for source, update in data.items():
                if source in ("model", "tools"):  # `source` captures node name
                    _render_completed_message(update["messages"][-1])


class ResponseSafety(BaseModel):
    """Evaluate a response as safe or unsafe."""
    evaluation: Literal["safe", "unsafe"] = "safe"


class A:
    evaluation: Literal["safe", "unsafe"] = "unsafe"


def access_completed_messages():
    safety_model = init_chat_model("deepseek-chat")
    safety_guardrail_func = create_safety_guardrail(safety_model)
    agent = create_agent(
        model="deepseek-chat",
        tools=[get_weather],
        middleware=[safety_guardrail_func],
    )
    input_message = {"role": "user", "content": "What is the weather in Boston?"}
    for stream_mode, data in agent.stream(
            {"messages": [input_message]},
            stream_mode=["messages", "updates", "custom"],
    ):
        if stream_mode == "messages":
            token, metadata = data
            if isinstance(token, AIMessageChunk):
                _render_message_chunk(token)
        if stream_mode == "updates":
            for source, update in data.items():
                if source in ("model", "tools"):
                    _render_completed_message(update["messages"][-1])
        if stream_mode == "custom":
            # access completed message in stream
            print(f"Tool calls: {data.tool_calls}")


def create_safety_guardrail(safety_model):
    @after_agent(can_jump_to=["end"])
    def safety_guardrail(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        """Model-based guardrail: Use an LLM to evaluate response safety."""
        stream_writer = get_stream_writer()
        # Get the model response
        if not state["messages"]:
            return None

        last_message = state["messages"][-1]
        if not isinstance(last_message, AIMessage):
            return None

        # Use another model to evaluate safety
        model_with_tools = safety_model.bind_tools([ResponseSafety], tool_choice="any")
        result = model_with_tools.invoke(
            [
                {
                    "role": "system",
                    "content": "Evaluate this AI response as generally safe or unsafe."
                },
                {
                    "role": "user",
                    "content": f"AI response: {last_message.text}"
                }
            ]
        )
        stream_writer(result)

        tool_call = result.tool_calls[0]
        if tool_call["args"]["evaluation"] == "unsafe":
            last_message.content = "I cannot provide that response. Please rephrase your request."

        return None

    return safety_guardrail


if __name__ == '__main__':
    load_dotenv()
    agent = create_agent("deepseek-chat", tools=[get_weather])
    # stream_tool_calls(agent)
    access_completed_messages()
