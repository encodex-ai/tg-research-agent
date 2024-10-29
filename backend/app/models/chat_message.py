from datetime import datetime
from bson import ObjectId

class ChatMessage:
    def __init__(self, user_id, role, content, message_id=None, timestamp=None):
        self.message_id = message_id or str(ObjectId())
        self.user_id = user_id
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.utcnow()

    @classmethod
    def from_dict(cls, data):
        return cls(
            message_id=data.get('_id'),
            user_id=data['user_id'],
            role=data['role'],
            content=data['content'],
            timestamp=data.get('timestamp')
        )

    def to_dict(self):
        return {
            '_id': self.message_id,
            'user_id': self.user_id,
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp
        }
