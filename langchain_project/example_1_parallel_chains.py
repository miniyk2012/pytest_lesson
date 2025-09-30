import time

from langchain_core.runnables import RunnableParallel, RunnableConfig
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.callbacks.stdout import StdOutCallbackHandler

from langchain_project.util import init_model


def joke(llm):
    prompt = ChatPromptTemplate.from_template("给我讲一个关于 {topic} 的笑话")
    return prompt | llm


def poem(llm):
    prompt = (
        ChatPromptTemplate.from_template("write a 2-line poem about {topic}")
    )
    return prompt | llm


class MyCustomHandler(StdOutCallbackHandler):

    def on_llm_start(self, serialized, prompts, **kwargs):
        print(f"{time.time()=}, LLM 开始运行，输入提示:{prompts}")

    def on_llm_end(self, response, **kwargs):
        print(f"{time.time()=}, LLM 运行结束，输出:{response.generations[0][0].text}")


def main():
    llm = init_model()
    joke_chain = joke(llm)
    poem_chain = poem(llm)
    explicit_parallel = RunnableParallel(
        joke=joke_chain,
        poem=poem_chain
    )
    resp = explicit_parallel.invoke({"topic": "程序员"}, config=RunnableConfig(callbacks=[MyCustomHandler()]))
    print("result joke: ", resp['joke'].content)
    print("诗歌:")
    print("result poem: ", resp['poem'].content)


if __name__ == '__main__':
    main()
