# -*- coding: utf-8 -*-
import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.load.dump import dumpd, dumps
from langchain_core.load.load import load, loads

from langchain_project.util import init_model, init_openai_model


def foo():
    prompt = ChatPromptTemplate.from_template("讲一个关于 {topic} 的笑话")

    # 将 prompt 对象转换为字典（使用 LangChain 官方序列化，包含模板内容）
    prompt_dict = dumpd(prompt)
    assert isinstance(prompt_dict, dict)

    # 打印（确保中文不乱码）
    print(json.dumps(prompt_dict, ensure_ascii=False, indent=2))

    # 将字典转换回 prompt 对象
    loaded_prompt = load(prompt_dict)
    assert loaded_prompt == prompt

def foo2():
    model = init_openai_model()
    model_dict = dumpd(model)
    assert isinstance(model_dict, dict)

    loaded_model = load(model_dict)
    print(loaded_model)


def bar():
    # 1. 构建一个 LCEL 链：Prompt -> Model -> Output Parser
    prompt = ChatPromptTemplate.from_template("写一首关于 {topic} 的诗")
    model = init_openai_model()
    parser = StrOutputParser()
    chain = prompt | model | parser

    response = chain.stream({"topic": "月光"})
    for chunk in response:
        print(chunk, end="", flush=True)
    print("\n--- 来自原始链的输出 ---")
    print("-" * 30)

    print("--- 原始的 LCEL 链 ---")
    # 打印链的结构
    try:
        for i, step in enumerate(chain.get_graph().nodes.values()):
            print(f"Step {i + 1}: {step.name}")
    except Exception:
        print("无法直接打印图结构，但链已创建。")
    print(chain.last.lc_secrets)
    print("-" * 30)

    # 2. 序列化 chain
    chain_json = dumps(chain, pretty=True)

    print("\n--- 保存的 JSON 内容 (部分) ---")
    preview = chain_json[:1000]
    print(preview + ("\n..." if len(chain_json) > 1000 else ""))
    print("-" * 30)

    # 3. 反序列化 chain
    loaded_chain = loads(chain_json)

    print("\n--- 加载的 LCEL 链 ---")
    try:
        for i, step in enumerate(loaded_chain.get_graph().nodes.values()):
            print(f"Step {i + 1}: {step.name}")
    except Exception:
        print("无法直接打印图结构，但链已从 JSON 成功加载。")
    print("-" * 30)

    # 4. 验证加载的链
    print("\n--- 验证加载的链是否能正常工作 ---")
    print("调用加载的链 (topic='月光')...")
    response = loaded_chain.invoke({"topic": "月光"})

    print("\n--- 来自加载链的输出 ---")
    print(response)
    print("-" * 30)

    print("\n结论: 序列化和反序列化使得完整的、可执行的链可以被轻松保存和复用。")


if __name__ == '__main__':
    # foo2()
    bar()
