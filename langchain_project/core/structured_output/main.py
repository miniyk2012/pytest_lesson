from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain.agents import create_agent

class ContactInfo(BaseModel):
    """Contact information for a person."""
    name: str = Field(description="The name of the person")
    email: str = Field(description="The email address of the person")
    phone: str = Field(description="The phone number of the person")


if __name__ == '__main__':
    load_dotenv()
    agent = create_agent(
        model="deepseek-chat",
        response_format=ContactInfo  # Auto-selects ProviderStrategy
    )

    result = agent.invoke({
        "messages": [
            {"role": "user", "content": "Extract contact info from: John Doe, john@example.com, (555) 123-4567"}]
    })

    print(type(result["structured_response"]), result["structured_response"])