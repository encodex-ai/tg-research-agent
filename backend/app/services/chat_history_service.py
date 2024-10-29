from typing import List
from datetime import datetime, timezone

from langchain_core.messages import ChatMessage

from app.database.mongodb import mongo_db
from app.models.chat_history import DbChatMessage


class ChatHistoryService:
    def __init__(self):
        self.collection = "chat_messages"

    def add_message(
        self, user_id: str, role: str, content: str, is_clarification: bool = False
    ) -> DbChatMessage:
        message = DbChatMessage(
            user_id=user_id,
            role=role,
            content=content,
            is_clarification=is_clarification,
            timestamp=datetime.now(timezone.utc),
        )
        mongo_db.insert_one(self.collection, message.to_dict())
        return message

    def get_chat_history(self, user_id: str, limit: int = 10) -> List[DbChatMessage]:
        messages = mongo_db.find(self.collection, {"user_id": user_id})
        sorted_messages = sorted(messages, key=lambda x: x["timestamp"], reverse=True)[
            :limit
        ]
        return [DbChatMessage.from_dict(m) for m in reversed(sorted_messages)]

    def get_langchain_chat_history(
        self, user_id: str, limit: int = 10
    ) -> List[ChatMessage]:
        chat_messages = self.get_chat_history(user_id, limit)
        return [msg.to_langchain_message() for msg in chat_messages]

    def clear_all_chat_history(self, user_id: str) -> None:
        # We just need to change all the user_id to None for the messages that have this user_id
        mongo_db.update_many(
            self.collection, {"user_id": user_id}, {"$set": {"user_id": None}}
        )

    def get_message(self, message_id: str) -> DbChatMessage:
        message_data = mongo_db.find_one(self.collection, {"_id": message_id})
        return DbChatMessage.from_dict(message_data) if message_data else None

    def update_message(self, message_id: str, content: str) -> None:
        mongo_db.update_one(
            self.collection, {"_id": message_id}, {"$set": {"content": content}}
        )

    def delete_message(self, message_id: str) -> None:
        mongo_db.delete_one(self.collection, {"_id": message_id})
