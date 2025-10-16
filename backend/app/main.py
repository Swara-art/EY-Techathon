from fastapi import FastAPI
from .database import Base, engine
from .routers import providers, validate, reports

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AutoValidate.AI")

app.include_router(providers.router)
app.include_router(validate.router)
app.include_router(reports.router)

@app.get("/")
def root():
    return {"ok": True, "service": "AutoValidate.AI"}
