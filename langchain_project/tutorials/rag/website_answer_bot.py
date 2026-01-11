import json  # noqa
import os
from pathlib import Path  # noqa
from tempfile import NamedTemporaryFile  # noqa

import bs4
import requests  # noqa
from gne import GeneralNewsExtractor  # noqa
from langchain_community.document_loaders import JSONLoader  # noqa
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_milvus import Milvus
from langchain.tools import tool
from langchain.agents import create_agent
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_project.utils.langsmith import new_project

embeddings = OpenAIEmbeddings(
    model="qwen/qwen3-embedding-8b",
    api_key=os.getenv("OPENROUTER_API_KEY", ""),
    base_url="https://openrouter.ai/api/v1",
)
URI = "./website_data.db"
vector_store = Milvus(
    embedding_function=embeddings,
    connection_args={"uri": URI},
    index_params={"index_type": "FLAT", "metric_type": "L2"},
)


# Construct a tool for retrieving context
@tool(response_format="content_and_artifact")
def retrieve_context(query: str):
    """Retrieve information to help answer a query."""
    retrieved_docs = vector_store.similarity_search(query, k=2)
    serialized = "\n\n".join(
        (f"Source: {doc.metadata}\nContent: {doc.page_content}")
        for doc in retrieved_docs
    )
    return serialized, retrieved_docs


def index_website():
    # Load and chunk contents of the blog
    loader = WebBaseLoader(
        web_paths=("https://www.siwei.io/fusion-graphrag-2025/",),
        bs_kwargs=dict(
            parse_only=bs4.SoupStrainer(
                class_=("content", "post-content", "post-title", "post-header")
            )
        ),
    )
    # use gen to
    # html = requests.get("https://www.siwei.io/fusion-graphrag-2025/").text
    # extractor = GeneralNewsExtractor()
    # result = extractor.extract(html, noise_node_list=['//div[@class="comment-list"]'])
    # with NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
    #     temp_file.write(json.dumps(result))
    #     temp_path = Path(temp_file.name)
    #     loader = JSONLoader(file_path=temp_path, jq_schema='.', text_content=False)
    docs = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    all_splits = text_splitter.split_documents(docs)
    # Index chunks
    vector_store.drop()
    _ = vector_store.add_documents(documents=all_splits)


def main():
    load_dotenv()
    new_project("Website Answer Bot")
    tools = [retrieve_context]
    # If desired, specify custom instructions
    prompt = (
        "You have access to a tool that retrieves context from a blog post. "
        "Only Use the tool to help answer user queries, don't use other knowledge."
    )
    llm = ChatOpenAI(model="deepseek-chat")
    agent = create_agent(llm, tools, system_prompt=prompt)
    query = ("RAG的挑战有哪些?\n\n"
             "根据这些挑战, 博客中给出了什么解决方案?")
    for step in agent.stream(
            {"messages": [{"role": "user", "content": query}]},
            stream_mode="values",
    ):
        step["messages"][-1].pretty_print()

from langchain.agents.middleware import dynamic_prompt, ModelRequest

@dynamic_prompt
def prompt_with_context(request: ModelRequest) -> str:
    last_query = request.messages[-1].text   # 拿到原始问题

    docs = vector_store.similarity_search(last_query, k=2)
    docs_content = "\n\n".join(doc.page_content for doc in docs)

    system_message = (
        "You are a helpful assistant. Use the following context in your response:"
        f"\n\n{docs_content}"
    )
    print("last_query:", last_query)
    print("system_message:", system_message)
    return system_message

def fixed_one_search():
    """将问题通过查询向量数据库只检索一次, 然后将结果通过动态system prompt传入模型"""
    load_dotenv()
    new_project("Website Answer Bot(fixed)")

    llm = ChatOpenAI(model="deepseek-chat")
    agent = create_agent(llm, middleware=[prompt_with_context])
    query = ("RAG的挑战有哪些?")
    for step in agent.stream(
            {"messages": [{"role": "user", "content": query}]},
            stream_mode="values",
    ):
        step["messages"][-1].pretty_print()


if __name__ == '__main__':
    # index_website()
    main()
    # fixed_one_search()

