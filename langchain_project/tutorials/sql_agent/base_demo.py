import requests, pathlib

from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent

from langchain_project.utils import langsmith


def prepare_db():
    url = "https://storage.googleapis.com/benchmarks-artifacts/chinook/Chinook.db"
    local_path = pathlib.Path("Chinook.db")

    if local_path.exists():
        print(f"{local_path} already exists, skipping download.")
    else:
        response = requests.get(url)
        if response.status_code == 200:
            local_path.write_bytes(response.content)
            print(f"File downloaded and saved as {local_path}")
        else:
            print(f"Failed to download the file. Status code: {response.status_code}")

    db = SQLDatabase.from_uri("sqlite:///Chinook.db")

    print(f"Dialect: {db.dialect}")
    print(f"Available tables: {db.get_usable_table_names()}")
    print(f'Sample output: {db.run("SELECT * FROM Artist LIMIT 5;")}')
    return db



def run_agent(question: str):
    model, system_prompt, tools = prepare_agent()
    agent = create_agent(
        model,
        tools,
        system_prompt=system_prompt,
    )
    for step in agent.stream(
            {"messages": [{"role": "user", "content": question}]},
            stream_mode="values",
    ):
        step["messages"][-1].pretty_print()


def prepare_agent():
    load_dotenv()
    model = init_chat_model("deepseek-chat", model_provider="deepseek", temperature=0)
    db = prepare_db()
    system_prompt = """
    You are an agent designed to interact with a SQL database.
    Given an input question, create a syntactically correct {dialect} query to run,
    then look at the results of the query and return the answer. Unless the user
    specifies a specific number of examples they wish to obtain, always limit your
    query to at most {top_k} results.

    You can order the results by a relevant column to return the most interesting
    examples in the database. Never query for all the columns from a specific table,
    only ask for the relevant columns given the question.

    You MUST double check your query before executing it. If you get an error while
    executing a query, rewrite the query and try again.

    DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the
    database.

    To start you should ALWAYS look at the tables in the database to see what you
    can query. Do NOT skip this step.

    Then you should query the schema of the most relevant tables.
    """.format(
        dialect=db.dialect,
        top_k=5,
    )
    toolkit = SQLDatabaseToolkit(db=db, llm=model)

    tools = toolkit.get_tools()

    for tool in tools:
        print(f"{tool.name}: {tool.description}\n")
    return model, system_prompt, tools


def main():
    langsmith.new_project("sql agent")
    question = "Which genre on average has the longest tracks?"
    run_agent(question)


if __name__ == '__main__':
    main()
