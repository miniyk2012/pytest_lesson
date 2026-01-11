from langchain_core.runnables import RunnableParallel, RunnableLambda, RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from langchain_project.utils.model import init_model


def run_parallel():
    runnable = RunnableParallel(
        passed_through=RunnablePassthrough(),
        extra=RunnablePassthrough.assign(mult=lambda x: x["num"] * 3),
        modified=lambda x: x["num"] + 1,
    )
    results = runnable.invoke({"num": 1})
    print(results)

    runnable2 = {
        "passed_through": RunnablePassthrough(),
        "extra": RunnablePassthrough.assign(mult=lambda x: x["num"] * 3),
        "modified": lambda x: x["num"] + 1,
    }
    # 据说不是并发执行的
    results2 = (runnable2 | RunnableLambda(lambda a: a)).invoke({"num": 1})
    print(results2)


def run_parallel_with_model():
    llm = init_model()
    joke_chain = (
            ChatPromptTemplate.from_template("讲一个关于 {topic} 的简短笑话")
            | llm
            | StrOutputParser()
    )
    poem_chain = (
            ChatPromptTemplate.from_template("写一首关于 {topic} 的宋词, 不允许有英文, 只允许全中文")
            | llm
            | StrOutputParser()
    )
    runnable = RunnableParallel(
        joke=joke_chain,
        poem=poem_chain,
    )
    results = runnable.stream({"topic": "恺宝柴犬狗子"})
    poem_result = ""
    joke_result = ""
    for chunk in results:
        if "poem" in chunk:
            poem_result += chunk["poem"]
        if "joke" in chunk:
            joke_result += chunk["joke"]

    print("【诗词】:\n", poem_result)
    print("\n【笑话】:\n", joke_result)


if __name__ == '__main__':
    run_parallel()
    # run_parallel_with_model()
