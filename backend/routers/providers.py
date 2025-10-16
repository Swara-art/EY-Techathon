from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Provider
from ..schemas import ProviderOut

router = APIRouter(prefix="/providers", tags=["providers"])

@router.get("/", response_model=list[ProviderOut])
def list_providers(limit: int = 50, db: Session = Depends(get_db)):
    q = db.query(Provider).limit(limit).all()
    return q
