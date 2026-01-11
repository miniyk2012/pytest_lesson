from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Union
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy


class ContactInfo(BaseModel):
    name: str = Field(description="Person's name")
    email: str = Field(description="Email address")

class EventDetails(BaseModel):
    event_name: str = Field(description="Name of the event")
    date: str = Field(description="Event date")

if __name__ == '__main__':
    load_dotenv()
    agent = create_agent(
        model="deepseek-chat",
        tools=[],
        response_format=ToolStrategy(Union[ContactInfo, EventDetails])  # Default: handle_errors=True
    )
    
    results = agent.invoke({
        "messages": [{"role": "user", "content": "Extract info: John Doe (john@email.com) is organizing Tech Conference on March 15th"}]
    })
    for message in results["messages"]:
        message.pretty_print()
    print(type(results["structured_response"]), results["structured_response"])