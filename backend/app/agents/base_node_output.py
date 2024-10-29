from pydantic import BaseModel, Field


class BaseNodeOutput(BaseModel):
    summary: str = Field(description="A user-friendly summary of what the node did")
