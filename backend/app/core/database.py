from pymongo import MongoClient
from app.core.config import settings


class Database:
    client: MongoClient = None
    db = None

    def connect(self):
        self.client = MongoClient(settings.mongo_connection_string)
        self.db = self.client[settings.DB_NAME]
        print(f"✅ Connected to MongoDB: {settings.DB_NAME}")

    def close(self):
        if self.client:
            self.client.close()
            print("❌ Disconnected from MongoDB")
    
    def get_collection(self, name: str):
        """Получить коллекцию MongoDB"""
        if self.db is None:
            self.connect()
        return self.db[name]


db = Database()


def get_database():
    return db.db

