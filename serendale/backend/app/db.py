# app/db.py
import os
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import FastAPI

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGODB_DB", "providers_db")
COLL_NAME = os.getenv("MONGODB_COLLECTION", "providers")

mongo_client: AsyncIOMotorClient | None = None

async def connect_to_mongo(app: FastAPI):
    global mongo_client
    mongo_client = AsyncIOMotorClient(MONGODB_URI)
    app.state.mongo = mongo_client
    app.state.db = mongo_client[DB_NAME]
    app.state.providers = app.state.db[COLL_NAME]
    # helpful indexes
    await app.state.providers.create_index("npi", unique=True, sparse=True)
    await app.state.providers.create_index(
        [("name", 1), ("phone", 1), ("address", 1)], name="name_phone_address"
    )

async def close_mongo(app: FastAPI):
    global mongo_client
    if mongo_client:
        mongo_client.close()
        mongo_client = None

def get_collection(request) -> "AsyncIOMotorCollection":
    return request.app.state.providers
