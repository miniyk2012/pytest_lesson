from pprint import pprint

from dotenv import load_dotenv
from langchain.agents import create_agent
from langgraph.config import get_stream_writer



def get_weather(city: str) -> str:
    """Get weather for a given city."""
    writer = get_stream_writer()
    # stream any arbitrary data
    writer(f"Looking up data for city: {city}")
    writer(f"Acquired data for city: {city}")
    return f"It's always sunny in {city}!"

def updates_stream_mode_demo(agent):
    for chunk in agent.stream(
        {"messages": [{"role": "user", "content": "What is the weather in SF?"}]},
        stream_mode="updates",
    ):
        for step, data in chunk.items():
            print(f"step: {step}")
            print(f"content: {data['messages'][-1].content_blocks}")

def messages_stream_mode_demo(agent):
    for token, metadata in agent.stream(
            {"messages": [{"role": "user", "content": "What is the weather in SF?"}]},
            stream_mode="messages",
    ):
        print(f"node: {metadata['langgraph_node']}")
        print(f"content: {token.content_blocks}")
        print("\n")

def custom_stream_mode_demo(agent):
    for chunk in agent.stream(
            {"messages": [{"role": "user", "content": "What is the weather in SF?"}]},
            stream_mode="custom"
    ):
        print(chunk)

def multiple_stream_mode_demo(agent):
    for stream_mode, chunk in agent.stream(
            {"messages": [{"role": "user", "content": "What is the weather in SF?"}]},
            stream_mode=["updates", "custom"]
    ):
        print(f"stream_mode: {stream_mode}")
        if stream_mode == "updates":
            for step, data in chunk.items():
                print(f"step: {step}")
                print(f"content: {data['messages'][-1].content_blocks}")
        else:
            print(f"content: {chunk}")
        print("\n")

if __name__ == '__main__':
    load_dotenv()
    agent = create_agent(
        model="deepseek-chat",
        tools=[get_weather],
    )
    # updates_stream_mode_demo(agent)
    print("\n==============================\n")
    # messages_stream_mode_demo(agent)
    print("\n==============================\n")
    # custom_stream_mode_demo(agent)
    print("\n==============================\n")
    multiple_stream_mode_demo(agent)

