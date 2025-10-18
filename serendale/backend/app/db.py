# app/db.py
import os
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import FastAPI

# 1️⃣ Set up database details
MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb+srv://apoorvmk457_db_user:sQzvLm8lwiMVLRoK@techathon.npghn3t.mongodb.net/"
)
DB_NAME = os.getenv("MONGODB_DB", "providers_db")
COLL_NAME = os.getenv("MONGODB_COLLECTION", "providers")
mongo_client: AsyncIOMotorClient | None = None

# 2️⃣ Connect to MongoDB
async def connect_to_mongo(app: FastAPI):
    global mongo_client
    mongo_client = AsyncIOMotorClient(MONGODB_URI)
    app.state.mongo = mongo_client
    app.state.db = mongo_client[DB_NAME]
    app.state.providers = app.state.db[COLL_NAME]
    # create helpful indexes (for speed & avoiding duplicates)
    await app.state.providers.create_index("npi", unique=True, sparse=True)
    await app.state.providers.create_index(
        [("name", 1), ("phone", 1), ("address", 1)], name="name_phone_address"
    )

# 3️⃣ Disconnect from MongoDB
async def close_mongo(app: FastAPI):
    global mongo_client
    if mongo_client:
        mongo_client.close()
        mongo_client = None

# 4️⃣ Helper function to get the collection anywhere in code
def get_collection(request):
    return request.app.state.providers
