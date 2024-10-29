from datetime import datetime

from app.database.mongodb import mongo_db
from app.models.user import User


class UserService:
    def __init__(self):
        self.collection = "users"

    def create_user(self, user_data):
        if "user_id" not in user_data:
            raise ValueError("user_id is required")

        # Ensure user_id is a string
        user_data["user_id"] = str(user_data["user_id"])

        # Set default values if not provided
        user_data.setdefault("successful_reports", 0)
        user_data.setdefault("last_request", datetime.now())

        try:
            user = User(**user_data)
            mongo_db.insert_one(self.collection, user.to_dict())
            return user
        except Exception as e:
            raise ValueError(f"Error creating user: {str(e)}")

    def get_user(self, user_id):
        user_data = mongo_db.find_one(self.collection, {"user_id": user_id})
        return User.from_dict(user_data) if user_data else None

    def update_user(self, user_id, user_data):
        mongo_db.update_one(self.collection, {"user_id": user_id}, {"$set": user_data})
        return self.get_user(user_id)

    # We don't need to delete users, but we can if we want to
    def delete_user(self, user_id):
        mongo_db.delete_one(self.collection, {"user_id": user_id})
