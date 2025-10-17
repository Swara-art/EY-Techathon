# app/main.py
from fastapi import FastAPI
from .db import connect_to_mongo, close_mongo
from .routers import ingest  # ✅ If your folder name is routers
# or use `.routes` if it’s inside routes instead
from dotenv import load_dotenv
load_dotenv()
from fastapi.middleware.cors import CORSMiddleware



app = FastAPI(title="Provider Ingest API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all origins (for testing)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# include the routes
app.include_router(ingest.router)

# connect to MongoDB when app starts
@app.on_event("startup")
async def startup_event():
    await connect_to_mongo(app)

# close MongoDB when app shuts down
@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo(app)
