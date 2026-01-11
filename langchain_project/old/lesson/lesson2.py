from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from langchain_project.utils.model import init_model


def invoke():
    # 1. 定义提示模板
    prompt = ChatPromptTemplate.from_template("给我讲一个关于 {topic} 的笑话")
    # 3. 定义输出解析器
    output_parser = StrOutputParser()
    llm = init_model()
    # 4. 使用管道符 | 组合成链
    chain = prompt | llm | output_parser

    # 5. 调用链
    result = chain.invoke({"topic": "程序员"})
    print(result)


def stream():
    prompt = ChatPromptTemplate.from_template("帮我介绍一下{input}")
    output_parser = StrOutputParser()
    llm = init_model()
    chain = prompt | llm | output_parser
    stream_response = chain.stream({"input": "杨恺(我)"})
    for chunk in stream_response:
        # chunk 是一个字符串片段
        print(chunk, end="", flush=True)


if __name__ == '__main__':
    # invoke()
    stream()