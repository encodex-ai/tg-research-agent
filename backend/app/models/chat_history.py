from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId
from langchain_core.messages import ChatMessage


class DbChatMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: str(ObjectId()))
    user_id: str
    role: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    is_clarification: bool = Field(default=False)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

    @classmethod
    def from_dict(cls, data: dict) -> "DbChatMessage":
        if "_id" in data:
            data["message_id"] = str(data.pop("_id"))
        if "timestamp" in data and isinstance(data["timestamp"], str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)

    def to_dict(self) -> dict:
        return self.model_dump(by_alias=True, exclude_unset=True)

    def to_langchain_message(self) -> ChatMessage:
        return ChatMessage(
            role=self.role,
            content=self.content,
            additional_kwargs={"is_clarification": self.is_clarification},
        )

    @classmethod
    def from_langchain_message(
        cls, message: ChatMessage, user_id: str
    ) -> "DbChatMessage":
        return cls(
            user_id=user_id,
            role=message.role,
            content=message.content,
            is_clarification=message.additional_kwargs.get("is_clarification", False),
        )
