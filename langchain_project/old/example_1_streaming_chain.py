import time
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.output_parsers import JsonOutputParser

from langchain_project.utils.model import init_model


def bar():
    """
    本示例将对比 `invoke` 和 `stream` 两种调用方式的区别。
    我们将创建一个简单的链，并分别使用两种方式调用它，以观察其行为和性能。
    """
    # 创建一个简单的链: Prompt -> Model -> Output Parser
    prompt = ChatPromptTemplate.from_template(
        "写一首关于 {topic} 的五行诗"
    )
    model = init_model()
    output_parser = StrOutputParser()
    chain = prompt | model | output_parser

    topic = "夜晚的星空"
    # print("--- 1. 使用 invoke() 调用 (一次性返回) ---")
    # start_time = time.time()
    #
    # # invoke 会阻塞，直到收到模型的完整回复
    # response = chain.invoke({"topic": topic})
    #
    # end_time = time.time()
    # print(f"invoke() 调用耗时: {end_time - start_time:.2f} 秒")
    # print("\n[模型完整输出]\n")
    # print(response)
    # print("-" * 30)

    # --- 2. 使用 stream() 调用 ---
    print("\n--- 2. 使用 stream() 调用 (逐块返回) ---")
    start_time = time.time()

    # stream 会立即返回一个迭代器，第一个 token 的返回时间非常快
    stream = chain.stream({"topic": topic})

    print("\n[模型流式输出]\n")
    chunks = []
    first_chunk_time = None
    for chunk in stream:
        chunks.append(chunk)
        if first_chunk_time is None:
            first_chunk_time = time.time()
        # 逐块打印，flush=True 确保立即显示
        print(chunk, end="", flush=True)

    end_time = time.time()
    print("\n")  # 换行
    if first_chunk_time:
        print(f"stream() 首个 chunk 响应时间: {first_chunk_time - start_time:.2f} 秒")
    print(f"stream() 总耗时: {end_time - start_time:.2f} 秒")
    print("-" * 30)


def main():
    import asyncio
    asyncio.run(foo())
    bar()


async def foo():
    model = init_model()
    chain = (
            model | JsonOutputParser()
    )  # Due to a bug in older versions of Langchain, JsonOutputParser did not stream results from some models
    async for text in chain.astream(
            "output a list of the countries france, spain and japan and their populations in JSON format. "
            'Use a dict with an outer key of "countries" which contains a list of countries. '
            "Each country should have the key `name` and `population`"
    ):
        print(text, end="|", flush=True)


if __name__ == '__main__':
    main()
