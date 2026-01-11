import requests
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langchain.tools import tool
from markdownify import markdownify

ALLOWED_DOMAINS = ["https://langchain-ai.github.io/"]
LLMS_TXT = 'https://langchain-ai.github.io/langgraph/llms.txt'


@tool
def fetch_documentation(url: str) -> str:
    """Fetch and convert documentation from a URL, maybe return error msg if not connected."""
    if not any(url.startswith(domain) for domain in ALLOWED_DOMAINS):
        return (
            "Error: URL not allowed. "
            f"Must start with one of: {', '.join(ALLOWED_DOMAINS)}"
        )
    response = requests.get(url, timeout=10.0)
    try:
        response.raise_for_status()
    except requests.HTTPError as e:
        return f"Error fetching documentation: {e}"
    return markdownify(response.text)


def main():
    # We will fetch the content of llms.txt, so this can
    # be done ahead of time without requiring an LLM request.
    load_dotenv()
    llms_txt_content = requests.get(LLMS_TXT).text

    # System prompt for the agent
    system_prompt = f"""
    You are an expert Python developer and technical assistant.
    Your primary role is to help users with questions about LangGraph and related tools.
    
    Instructions:
    
    1. If a user asks a question you're unsure about — or one that likely involves API usage,
       behavior, or configuration — you MUST use the `fetch_documentation` tool to consult the relevant docs.
    2. When citing documentation, summarize clearly and include relevant context from the content.
    3. Do not use any URLs outside of the allowed domain.
    4. If a documentation fetch fails, tell the user and proceed with your best expert understanding.
    
    You can access official documentation from the following approved sources:
    
    {llms_txt_content}
    
    You MUST consult the documentation to get up to date documentation
    before answering a user's question about LangGraph.
    
    Your answers should be clear, concise, and technically accurate.
    """

    tools = [fetch_documentation]

    model = init_chat_model("deepseek-chat", max_tokens=1024)

    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
        name="Agentic RAG",
    )

    # 使用 stream 方式获取完整响应
    final_content = ""
    for chunk in agent.stream(
            {'messages': [
                HumanMessage(content=(
                        "Write a short example of a langgraph agent using the "
                        "prebuilt create react agent. the agent should be able "
                        "to look up stock pricing information."))
            ]
            },
            stream_mode="updates"
    ):
        for node, update in chunk.items():
            if node == "model" and "messages" in update:
                msg = update["messages"][-1]
                if msg.content and not msg.tool_calls:  # Final AI response, 非function call
                    final_content += msg.content
                    print(f"{msg.content}", end='', flush=True)
                    break  # Or continue to accumulate if multi-step

    print(f"\n完整内容长度: {len(final_content)}")


if __name__ == '__main__':
    main()
