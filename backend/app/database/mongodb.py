from pymongo import MongoClient
import os
import logging
from app.config import Config


COLLECTIONS = {"agents": "agents", "users": "users", "messages": "messages"}

# Set pymongo logging level to WARNING
logging.getLogger("pymongo").setLevel(logging.WARNING)


class MongoDB:
    def __init__(self):
        self.client = None
        self.db = None

    def init_app(self):
        mongodb_uri = Config.MONGODB_ATLAS_URI or os.environ.get("MONGODB_ATLAS_URI")
        if not mongodb_uri:
            raise ValueError("MONGODB_ATLAS_URI is not set")

        db_name = Config.DB_NAME or os.environ.get("DB_NAME", "dev")

        self.client = MongoClient(mongodb_uri)
        self.db = self.client.get_database(db_name)
        logging.info(f"Connected to database: {db_name}")

    def insert_one(self, collection, document):
        return self.db[collection].insert_one(document)

    def find_one(self, collection, query):
        return self.db[collection].find_one(query)

    def update_one(self, collection, query, update):
        return self.db[collection].update_one(query, update)

    def delete_one(self, collection, query):
        return self.db[collection].delete_one(query)

    def find(self, collection, query=None):
        return self.db[collection].find(query or {})

    def update_many(self, collection, query, update):
        return self.db[collection].update_many(query, update)

    def delete_many(self, collection, query):
        return self.db[collection].delete_many(query)


# Create a global instance of MongoDB
mongo_db = MongoDB()
