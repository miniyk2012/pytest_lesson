from typing import Any

from dotenv import load_dotenv
from dataclasses import dataclass
from langchain_openai import ChatOpenAI
from langchain.chat_models import BaseChatModel
from langgraph.store.memory import InMemoryStore
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState

USER_DATABASE = {
    "user123": {
        "name": "Alice Johnson",
        "account_type": "Premium",
        "balance": 5000,
        "email": "alice@example.com"
    },
    "user456": {
        "name": "Bob Smith",
        "account_type": "Standard",
        "balance": 1200,
        "email": "bob@example.com"
    }
}


@dataclass
class UserContext:
    user_id: str


@tool
def get_account_info(runtime: ToolRuntime[UserContext]) -> str:
    """Get the current user's account information."""
    user_id = runtime.context.user_id

    if user_id in USER_DATABASE:
        user = USER_DATABASE[user_id]
        return f"Account holder: {user['name']}\nType: {user['account_type']}\nBalance: ${user['balance']}"
    return "User not found"


def context_demo(model: BaseChatModel):
    agent = create_agent(
        model,
        tools=[get_account_info],
        context_schema=UserContext,
        system_prompt="You are a financial assistant."
    )

    print("--- user exists ---")
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "What's my current balance?"}]},
        context=UserContext(user_id="user123")
    )
    print(result["messages"][-1].content)

    print("--- user not found ---")
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "What's my current balance?"}]},
        context=UserContext(user_id="xxx")
    )
    print(result["messages"][-1].content)


# Access memory
@tool
def get_user_info(user_id: str, runtime: ToolRuntime) -> str:
    """Look up user info."""
    store = runtime.store
    user_info = store.get(("users",), user_id)
    return str(user_info.value) if user_info else "Unknown user"


# Update memory
@tool
def save_user_info(user_id: str, user_info: dict[str, Any], runtime: ToolRuntime) -> str:
    """Save user info."""
    store = runtime.store
    store.put(("users",), user_id, user_info)
    return "Successfully saved user info."


def store_demo(model: BaseChatModel):
    store = InMemoryStore()
    checkpointer = InMemorySaver()

    agent = create_agent(
        model,
        tools=[get_user_info, save_user_info],
        store=store,
        checkpointer=checkpointer,
        system_prompt="You are a helpful assistant that saves and retrieves user information."
    )
    config = {"configurable": {"thread_id": "1"}}
    # First session: save user info
    agent.invoke({
        "messages": [{"role": "user",
                      "content": "Save the following user: userid: abc123, name: Foo, age: 25, email: foo@langchain.dev"}],
    },
        config=config,
    )

    # Second session: get user info
    ret = agent.invoke({
        "messages": [{"role": "user", "content": "Get user info for user with id 'abc123'"}],
    },
        config={"configurable": {"thread_id": "2"}}   # 这个invoke就没有被state保存下来, 因为thread_id不同
    )

    print(ret["messages"][-1].content)
    ret = agent.invoke({"messages": ["我问了你几个问题啦?"]}, config=config)
    print(ret["messages"][-1].content)

class CustomState(AgentState):  # Extends messages
    user_id: str
    cost: float

if __name__ == '__main__':
    load_dotenv()
    model = ChatOpenAI(model="deepseek-chat")
    # context_demo(model)
    store_demo(model)
