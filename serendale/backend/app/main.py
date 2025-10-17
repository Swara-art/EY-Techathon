# app/main.py
from fastapi import FastAPI
from .db import connect_to_mongo, close_mongo
from .routers import ingest

app = FastAPI(title="Provider Ingest")
app.include_router(ingest.router)

@app.on_event("startup")
async def _startup():
    await connect_to_mongo(app)

@app.on_event("shutdown")
async def _shutdown():
    await close_mongo(app)
