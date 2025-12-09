
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

class Database:
    client: AsyncIOMotorClient = None
    db = None

    def connect(self):
        self.client = AsyncIOMotorClient(settings.MONGODB_URI)
        self.db = self.client[settings.DB_NAME]
        print(f"✅ Connected to MongoDB: {settings.DB_NAME}")

    def close(self):
        if self.client:
            self.client.close()
            print("❌ Disconnected from MongoDB")

db = Database()

async def get_database():
    return db.db

