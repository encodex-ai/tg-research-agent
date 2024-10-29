from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class User(BaseModel):
    user_id: str
    first_name: str
    last_name: Optional[str] = None
    successful_reports: int = Field(default=0)
    last_request: Optional[datetime] = Field(default_factory=datetime.now)
    agent_id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        return cls(**data)

    def to_dict(self) -> dict:
        return self.model_dump(by_alias=True)
