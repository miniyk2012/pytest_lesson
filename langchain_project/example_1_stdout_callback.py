from langchain.callbacks.base import BaseCallbackHandler
from langchain_core.prompts import ChatPromptTemplate

from langchain_project.util import init_model, init_openai_model


class MyCustomHandler(BaseCallbackHandler):
    def on_llm_start(self, serialized, prompts, **kwargs):
        print(f"LLM 开始运行，输入提示: {prompts}")

    def on_llm_end(self, response, **kwargs):
        print(f"LLM 运行结束，输出: {response}")


if __name__ == '__main__':
    callbacks = [MyCustomHandler()]
    llm = init_openai_model(callbacks=callbacks)
    prompt = ChatPromptTemplate.from_template("What is 1 + {number}?")

    chain = prompt | llm

    result = chain.invoke({"number": "200"})
    print(result.content)
