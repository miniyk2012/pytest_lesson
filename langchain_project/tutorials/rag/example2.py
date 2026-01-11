import os
from typing import Any

import bs4
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_milvus import Milvus
from langchain.agents import create_agent
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain.agents.middleware import AgentMiddleware, AgentState
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
    docs = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    all_splits = text_splitter.split_documents(docs)
    # Index chunks
    vector_store.drop()
    _ = vector_store.add_documents(documents=all_splits)

class State(AgentState):
    context: list[Document]

class RetrieveDocumentsMiddleware(AgentMiddleware[State]):
    state_schema = State
    def before_model(self, state: AgentState) -> dict[str, Any] | None:
        """Logic to run before the model is called.

        Async version is `abefore_model`
        """
        last_message = state["messages"][-1]
        retrieved_docs = vector_store.similarity_search(last_message.text)
        docs_content = "\n\n".join(doc.page_content for doc in retrieved_docs)
        augmented_message_content = (
            f"{last_message.text}\n\n"
            "Use the following context to answer the query:\n"
            f"{docs_content}"
        )
        return {
            "messages": [last_message.model_copy(update={"content": augmented_message_content})],
            "context": retrieved_docs  # artifact
        }

def main():
    load_dotenv()
    new_project("Website Answer Bot")
    # If desired, specify custom instructions
    prompt = (
        "You have access to a tool that retrieves context from a blog post. "
        "Only Use the tool to help answer user queries, don't use other knowledge."
    )
    llm = ChatOpenAI(model="deepseek-chat")
    agent = create_agent(llm, middleware=[RetrieveDocumentsMiddleware()])
    query = ("RAG的挑战有哪些?")
    for step in agent.stream(
            {"messages": [{"role": "user", "content": query}]},
            stream_mode="values",
    ):
        step["messages"][-1].pretty_print()





if __name__ == '__main__':
    main()

