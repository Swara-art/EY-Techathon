# db.py
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()  # MUST be at the very top

# --- Step 2: Read environment variables ---
MONGO_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("MONGODB_DB")
COLLECTION_NAME = os.getenv("MONGODB_COLLECTION")

# --- Step 3: Safety check ---
if not MONGO_URI or not DB_NAME or not COLLECTION_NAME:
    raise ValueError(
        "Please check your .env file: MONGODB_URI, MONGODB_DB, MONGODB_COLLECTION must be set"
    )

# --- Step 4: Initialize MongoDB client ---
mongo_client = AsyncIOMotorClient(MONGO_URI)
mongo_db = mongo_client[DB_NAME]

print(f"✅ Connected to MongoDB database: {DB_NAME}, collection: {COLLECTION_NAME}")

# --- Step 5: Function to get collection ---
def get_collection():
    """
    Returns the MongoDB collection object
    """
    return mongo_db[COLLECTION_NAME]

# --- Optional startup/shutdown hooks for FastAPI ---
async def connect_to_mongo():
    try:
        await mongo_client.admin.command("ping")
        print("MongoDB connection successful")
    except Exception as e:
        print("MongoDB connection failed:", e)

async def close_mongo():
    mongo_client.close()
    print("MongoDB connection closed")
