from dotenv import load_dotenv
from langchain.chat_models import init_chat_model, BaseChatModel
from langchain.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage


def basic(model: BaseChatModel):
    messages = [
        SystemMessage("You are a poetry expert"),
        HumanMessage("Write a haiku about spring"),
        AIMessage("Cherry blossoms bloom...")
    ]
    response = model.invoke(messages)  # Returns AIMessage
    print(type(response), response.content)

def ai_msg_usage(model: BaseChatModel):
    messages = [
        SystemMessage("你模拟一个富人"),
        HumanMessage("你最近赚了多少"),
        AIMessage("我赚的太多啦"),
        HumanMessage("详细说说(100字以内)"),
    ]
    response = model.invoke(messages)  # Returns AIMessage
    print(response.content)

def get_weather(location: str) -> str:
    """Get the weather at a location."""
    ...

def tool_msg(model: BaseChatModel):
    model_with_tools = model.bind_tools([get_weather])
    response = model_with_tools.invoke("What's the weather in Paris?")
    for tool_call in response.tool_calls:
        print(f"Tool: {tool_call['name']}")
        print(f"Args: {tool_call['args']}")
        print(f"ID: {tool_call['id']}")
    print(response.usage_metadata)

    # After a model makes a tool call, 模拟了工具调用
    # (Here, we demonstrate manually creating the messages for brevity)
    ai_message = AIMessage(
        content=[],
        tool_calls=[{
            "name": "get_weather",
            "args": {"location": "San Francisco"},
            "id": "call_123"
        }]
    )

    # Execute tool and create result message, 模拟了工具执行结果
    weather_result = "Sunny, 72°F"
    tool_message = ToolMessage(
        content=weather_result,
        tool_call_id="call_123"  # Must match the call ID
    )

    # Continue conversation
    messages = [
        HumanMessage("What's the weather in San Francisco?"),
        ai_message,  # Model's tool call
        tool_message,  # Tool execution result
    ]
    response = model.invoke(messages)  # Model processes the result
    print(response.content)


def stream_demo(model: BaseChatModel):
    for chunk in model.stream("Hi"):
        print(chunk.text, end='', flush=True)

def content_blocks():
    # String content
    human_message = HumanMessage("Hello, how are you?")

    # Provider-native format (e.g., OpenAI)
    human_message = HumanMessage(content=[
        {"type": "text", "text": "Hello, how are you?"},
        {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
    ])

    # List of standard content blocks
    human_message = HumanMessage(content_blocks=[
        {"type": "text", "text": "Hello, how are you?"},
        {"type": "image", "url": "https://example.com/image.jpg"},
    ])


    print("content_blocks是标准化后的内容, content则每个厂商会不同")
    message = AIMessage(
        content=[
            {"type": "thinking", "thinking": "...", "signature": "WaUjzkyp..."},
            {"type": "text", "text": "..."},
        ],
        response_metadata={"model_provider": "deepseek"}
    )
    print(type(message.content_blocks[0]), message.content_blocks)

    message = AIMessage(
        content=[
            {
                "type": "reasoning",
                "id": "rs_abc123",
                "summary": [
                    {"type": "summary_text", "text": "summary 1"},
                    {"type": "summary_text", "text": "summary 2"},
                ],
            },
            {"type": "text", "text": "...", "id": "msg_abc123"},
        ],
        response_metadata={"model_provider": "openai"}
    )
    print(type(message.content_blocks[0]), message.content_blocks)


if __name__ == '__main__':
    load_dotenv()
    model = init_chat_model("deepseek-chat", model_provider="deepseek", temperature=0)
    # basic(model)
    # ai_msg_usage(model)
    # tool_msg(model)
    # stream_demo(model)
    content_blocks()