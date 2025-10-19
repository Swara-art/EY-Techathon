from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Import database functions AFTER loading .env
from .db import connect_to_mongo, close_mongo
from .routers import ingest

# Initialize FastAPI app
app = FastAPI(
    title=os.getenv("APP_NAME", "TechathonProject"),
    version="1.0.0",
    description="Techathon Project API"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ingest.router)

# Startup event - connect to MongoDB
@app.on_event("startup")
async def startup_event():
    try:
        await connect_to_mongo()
        print("✅ Startup complete - MongoDB connected")
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        raise

# Shutdown event - close MongoDB connection
@app.on_event("shutdown")
async def shutdown_event():
    try:
        await close_mongo()
        print("✅ Shutdown complete - MongoDB closed")
    except Exception as e:
        print(f"❌ Shutdown error: {e}")

# Root endpoint for testing
@app.get("/")
async def root():
    return {"message": "Welcome to Techathon API"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}