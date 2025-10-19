from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os
from typing import Dict, Any
import aiofiles
import hashlib
from datetime import datetime
from pathlib import Path

# Load .env file - check multiple possible locations
possible_env_paths = [
    Path(__file__).parent.parent / ".env",  # backend/.env
    Path(__file__).parent.parent.parent / ".env",  # serendale/.env
    Path.cwd() / ".env",  # current working directory
]

env_loaded = False
for env_path in possible_env_paths:
    if env_path.exists():
        print(f"✅ Found .env at: {env_path}")
        load_dotenv(dotenv_path=env_path, verbose=True)
        env_loaded = True
        break

if not env_loaded:
    print("⚠️  No .env file found in any expected location")
    print(f"Checked:\n" + "\n".join(str(p) for p in possible_env_paths))

# Read environment variables
MONGO_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("MONGODB_DB")
COLLECTION_NAME = os.getenv("MONGODB_COLLECTION")

# Debug output
print(f"DEBUG - MONGO_URI: {'Found' if MONGO_URI else 'NOT FOUND'}")
print(f"DEBUG - DB_NAME: {DB_NAME if DB_NAME else 'NOT FOUND'}")
print(f"DEBUG - COLLECTION_NAME: {COLLECTION_NAME if COLLECTION_NAME else 'NOT FOUND'}")

# Safety check
if not MONGO_URI or not DB_NAME or not COLLECTION_NAME:
    raise ValueError(
        f"❌ Environment variables not loaded!\n"
        f"MONGODB_URI: {'✅' if MONGO_URI else '❌'}\n"
        f"MONGODB_DB: {'✅' if DB_NAME else '❌'}\n"
        f"MONGODB_COLLECTION: {'✅' if COLLECTION_NAME else '❌'}\n"
        f"\nMake sure .env file exists in backend/ folder with these variables set."
    )

# Initialize MongoDB client
mongo_client = AsyncIOMotorClient(MONGO_URI)
mongo_db = mongo_client[DB_NAME]

print(f"✅ MongoDB client initialized for database: {DB_NAME}, collection: {COLLECTION_NAME}")

# Function to get collection
def get_collection():
    """Returns the MongoDB collection object"""
    return mongo_db[COLLECTION_NAME]

# Startup/shutdown hooks
async def connect_to_mongo():
    """Test the MongoDB connection"""
    try:
        await mongo_client.admin.command("ping")
        print("✅ MongoDB connection successful")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        raise

async def close_mongo():
    """Close the MongoDB connection"""
    mongo_client.close()
    print("❌ MongoDB connection closed")