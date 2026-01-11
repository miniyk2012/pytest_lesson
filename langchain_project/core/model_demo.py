from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain.chat_models import init_chat_model, BaseChatModel
from langchain.messages import SystemMessage, HumanMessage, AIMessage


def invoke_demo(model: BaseChatModel):
    response = model.invoke("为什么天是蓝色的, 简短回答")
    print(response.content)

    # 将历史对话传入
    conversation = [
        SystemMessage("You are a helpful assistant that translates English to Chinese."),
        HumanMessage("Translate: I love programming."),
        AIMessage("我喜欢编程."),
        HumanMessage("Translate: I love building applications.")
    ]

    print("翻译:")
    response = model.invoke(conversation)
    print(type(response), '\n', response.content)


def stream_demo(model: BaseChatModel):
    response_stream = model.stream("请用中文描述一下人工智能的未来发展趋势, 分三点叙述")
    for chunk in response_stream:
        print(chunk.text, end='', flush=True)
    print()


def batch_demo(model: BaseChatModel):
    batch = [
        "为什么天是蓝的(100字以内)",
        "为啥水可以导电(100字以内)",
        "你好呀!(100字以内)"
    ]
    responses = model.batch_as_completed(batch)
    for response in responses:
        print(batch[response[0]], response[1].content)


def invocation(model: BaseChatModel):
    # print("---------------------------- invoke: ----------------------------")
    # invoke_demo(model)

    # print("---------------------------- stream: ----------------------------")
    # stream_demo(model)

    print("---------------------------- batch: ----------------------------")
    batch_demo(model)


from langchain.tools import tool


@tool
def get_weather(location: str) -> str:
    """Get the weather at a location."""
    return f"It's sunny in {location}."


def tool_calling(model: BaseChatModel):
    # tool_calls(model)
    # tool_execution_loop(model)
    # force_tool(model)
    parallel_tool_calling(model)


def tool_calls(model: BaseChatModel):
    print("--- see tool_calls when invoke ---")
    model_with_tools = model.bind_tools([get_weather])
    response = model_with_tools.invoke("What's the weather like in Boston?")
    for tool_call in response.tool_calls:
        print(type(tool_call))
        # View tool calls made by the model
        print(f"Tool: {tool_call['name']}")
        print(f"Args: {tool_call['args']}")
    print(response.content)


def tool_execution_loop(model: BaseChatModel):
    print("--- 笨办法, 需要人工取迭代调用 ---")
    model_with_tools = model.bind_tools([get_weather])
    messages = [{"role": "user", "content": "What's the weather in Boston?"}]
    ai_message = model_with_tools.invoke(messages)
    messages.append(ai_message)
    print(ai_message.text)
    for tool_call in ai_message.tool_calls:
        # Execute the tool with the generated arguments
        tool_result = get_weather.invoke(tool_call)
        print(f"{tool_call=}\n{tool_result=}")
        messages.append(tool_result)

    # Step 3: Pass results back to model for final response
    final_response = model_with_tools.invoke(messages)
    print(final_response.text)


def force_tool(model):
    print("""强制调用tool, 没必要自己去搞""")
    model_with_tools = model.bind_tools([get_weather], tool_choice="any")
    messages = [{"role": "user", "content": "What's the weather in Boston?"}]
    ai_message = model_with_tools.invoke(messages)
    for tool_call in ai_message.tool_calls:
        # 执行工具获取结果
        tool_result = get_weather.invoke(tool_call["args"]["location"])
        print(f"工具结果: {tool_result}")


def parallel_tool_calling(model: BaseChatModel):
    model_with_tools = model.bind_tools([get_weather])
    messages = ["What's the weather in Boston and Tokyo?"]
    response = model_with_tools.invoke(
        messages
    )
    messages.append(response)
    print(f"f{response.tool_calls=}\n{response.content}")

    results = []
    for tool_call in response.tool_calls:
        if tool_call['name'] == 'get_weather':
            result = get_weather.invoke(tool_call)
            messages.append(result)
        results.append(result)
    print(results)

    final_response = model_with_tools.invoke(messages)
    print(final_response.content)


class Actor(BaseModel):
    name: str
    role: str

class MovieDetails(BaseModel):
    title: str
    year: int
    cast: list[Actor]
    genres: list[str]
    budget: float | None = Field(None, description="票房收入(美元)")


def structured_output(model: BaseChatModel):
    model_with_structure = model.with_structured_output(MovieDetails, include_raw=True)
    response = model_with_structure.invoke("提供<泰坦尼克号>详情")
    print(type(response), response['parsed'])

if __name__ == '__main__':
    load_dotenv()
    model = init_chat_model("deepseek-chat", temperature=0)

    # invocation(model)

    # tool_calling(model)
    structured_output(model)
