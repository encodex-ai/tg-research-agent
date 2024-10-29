from datetime import datetime
from enum import Enum

from typing import Optional
from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"
    WAITING_FOR_INPUT = "waiting_for_input"


class Agent(BaseModel):
    agent_id: Optional[str] = None
    user_id: str
    name: str
    description: str
    status: AgentStatus = Field(default=AgentStatus.IDLE)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    error: Optional[str] = None
    current_node: Optional[str] = None
    result: Optional[str] = None
    followup_question: Optional[str] = None

    class Config:
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}

    def to_dict(self) -> dict:
        return self.model_dump(by_alias=True, exclude_none=True)

    @classmethod
    def from_dict(cls, data: dict) -> "Agent":
        if "_id" in data:
            del data["_id"]
        data["status"] = AgentStatus(data["status"])
        if data["created_at"] and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if data["updated_at"] and isinstance(data["updated_at"], str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        return cls(**data)
