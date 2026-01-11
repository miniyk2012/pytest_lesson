import os
from typing import Literal

from dotenv import load_dotenv
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.tools import tool
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings
from langgraph.graph import MessagesState
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from IPython.display import Image, display  # noqa
from pydantic import BaseModel, Field


def create_retrieve():
    urls = [
        "https://colobu.com/2025/01/30/some-notes-about-go-io-fs-package/",
        "https://colobu.com/2024/11/18/go-internal-ds-4-ary-heap/",
        "https://colobu.com/2024/11/17/heapmap/"
    ]

    docs = [WebBaseLoader(url).load() for url in urls]
    docs_list = [item for sublist in docs for item in sublist]
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=100, chunk_overlap=50
    )
    doc_splits = text_splitter.split_documents(docs_list)

    embeddings = OpenAIEmbeddings(
        model="qwen/qwen3-embedding-8b",
        api_key=os.getenv("OPENROUTER_API_KEY", ""),
        base_url="https://openrouter.ai/api/v1",
    )

    vectorstore = InMemoryVectorStore.from_documents(
        documents=doc_splits, embedding=embeddings
    )
    retriever = vectorstore.as_retriever()
    return retriever


def create_retrieve_blog_posts_tool(retriever):
    @tool
    def retrieve_blog_posts(query: str) -> str:
        """Search and return information about golang language."""
        docs = retriever.invoke(query)
        return "\n\n".join([doc.page_content for doc in docs])

    return retrieve_blog_posts


def try_receiver():
    retriever = create_retrieve()
    retrieve_blog_posts_tool = create_retrieve_blog_posts_tool(retriever)
    result = retrieve_blog_posts_tool.invoke({"query": "TDD思想驱动AI开发怎么实现"})
    print(result)


load_dotenv()
MODEL_REGISTRY = {
    "grade": init_chat_model("deepseek-chat", temperature=0),
    "response": init_chat_model("deepseek-chat", temperature=0)
}


def generate_query_or_respond(state: MessagesState):
    """Call the model to generate a response based on the current state. Given
        the question, it will decide to retrieve using the retriever tool, or simply respond to the user.
    """
    response_model = MODEL_REGISTRY["response"]
    retriever = create_retrieve()
    retrieve_blog_posts_tool = create_retrieve_blog_posts_tool(retriever)
    response = response_model.bind_tools([retrieve_blog_posts_tool]).invoke(state["messages"])
    return {"messages": [response]}


def generate_query():
    input = {
        "messages": [
            {
                "role": "user",
                "content": "美团的文章主要讲了什么内容",
            }
        ]
    }
    generate_query_or_respond(input)["messages"][-1].pretty_print()


class GradeDocuments(BaseModel):
    """Grade documents using a binary score for relevance check."""

    binary_score: str = Field(
        description="Relevance score: 'yes' if relevant, or 'no' if not relevant"
    )


def grade_documents(state: MessagesState) -> Literal["generate_answer", "rewrite_question"]:
    """Determine whether the retrieved documents are relevant to the question."""
    GRADE_PROMPT = (
        "你是一名评分人员，负责评估检索到的文档与用户问题的相关性。\n"
        "以下是检索到的文档：\n\n {context}\n\n"
        "以下是用户的问题：{question}\n"
        "如果文档与用户问题相关的关键词或语义信息强烈匹配，则判定该文档为相关。\n"
        "请给出二元评分结果，用 'yes' 或 'no' 表示该文档是否与问题相关。"
    )

    question = state["messages"][0].content
    context = state["messages"][-1].content
    prompt = GRADE_PROMPT.format(question=question, context=context)
    response = (
        MODEL_REGISTRY["grade"]
        .with_structured_output(GradeDocuments).invoke(
            [{"role": "user", "content": prompt}]
        )
    )
    score = response.binary_score
    if score == "yes":
        return "generate_answer"
    else:
        return "rewrite_question"


def rewrite_question(state: MessagesState):
    """Rewrite the original user question."""
    REWRITE_PROMPT = (
        "观察输入内容，并尝试推断其背后的语义意图/含义。\n"
        "原始问题如下："
        "\n ------- \n"
        "{question}"
        "\n ------- \n"
        "请构造一个优化后的问题："
    )
    messages = state["messages"]
    question = messages[0].content  # 永远优化原始问题
    prompt = REWRITE_PROMPT.format(question=question)
    response = MODEL_REGISTRY["response"].invoke([{"role": "user", "content": prompt}])
    return {"messages": [HumanMessage(content=response.content)]}


def generate_answer(state: MessagesState):
    """Generate an answer."""
    GENERATE_PROMPT = (
        "你是一名问答任务助手。"
        "请利用以下检索到的上下文信息回答问题。"
        "如果不知道答案，只需说明你不知道即可。"
        "回答最多使用三句话，保持简洁明了。\n"
        "问题：{question} \n"
        "上下文：{context}"
    )

    question = state["messages"][0].content
    context = state["messages"][-1].content
    prompt = GENERATE_PROMPT.format(question=question, context=context)
    response = MODEL_REGISTRY["response"].invoke([{"role": "user", "content": prompt}])
    return {"messages": [response]}


def assemble_graph():
    workflow = StateGraph(MessagesState)
    retriever = create_retrieve()
    retrieve_blog_posts_tool = create_retrieve_blog_posts_tool(retriever)

    # Define the nodes we will cycle between
    workflow.add_node(generate_query_or_respond)
    workflow.add_node("retrieve", ToolNode([retrieve_blog_posts_tool]))
    workflow.add_node(rewrite_question)
    workflow.add_node(generate_answer)

    workflow.add_edge(START, "generate_query_or_respond")
    # Decide whether to retrieve
    workflow.add_conditional_edges(
        "generate_query_or_respond",
        # Assess LLM decision (call `retriever_tool` tool or respond to the user)
        tools_condition,
        {
            # Translate the condition outputs to nodes in our graph
            "tools": "retrieve",
            END: END,
        },
    )

    # Edges taken after the `action` node is called.
    workflow.add_conditional_edges(
        "retrieve",
        # Assess agent decision
        grade_documents,
    )
    workflow.add_edge("generate_answer", END)
    workflow.add_edge("rewrite_question", "generate_query_or_respond")
    # Compile
    graph = workflow.compile()
    return graph


def main():
    graph = assemble_graph()
    # png_data = graph.get_graph().draw_mermaid_png()
    # with open("workflow_graph.png", "wb") as f:
    #     f.write(png_data)
    for chunk in graph.stream(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": "请问golang中为什么timer使用四叉堆呢?",
                    }
                ]
            }
    ):
        for node, update in chunk.items():
            print("Update from node", node)
            update["messages"][-1].pretty_print()
            print("\n\n")


if __name__ == '__main__':
    # try_receiver()
    main()