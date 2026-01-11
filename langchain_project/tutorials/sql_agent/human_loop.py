from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent

from langgraph.types import Command

from langchain_project.tutorials.sql_agent.base_demo import prepare_agent
from langchain_project.utils.langsmith import new_project


def main():
    new_project("humanloop")
    model, system_prompt, tools = prepare_agent()
    agent = create_agent(
        model,
        tools,
        system_prompt=system_prompt,
        middleware=[
            HumanInTheLoopMiddleware(
                interrupt_on={"sql_db_query": True},
                description_prefix="Tool execution pending approval",
            ),
        ],
        checkpointer=InMemorySaver(),
    )
    question  = "Which genre on average has the longest tracks?"
    config = {"configurable": {"thread_id": "1"}}
    for step in agent.stream(
            {"messages": [{"role": "user", "content": question}]},
            config,
            stream_mode="values",
    ):
        if "__interrupt__" in step:
            print("INTERRUPTED1:")
            interrupt = step["__interrupt__"][0]
            for request in interrupt.value["action_requests"]:
                print(request["description"])
        elif "messages" in step:
            step["messages"][-1].pretty_print()
        else:
            pass


if __name__ == '__main__':
    main()
