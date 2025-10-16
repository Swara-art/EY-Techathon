from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Provider
from sqlalchemy import func

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/kpis")
def kpis(db: Session = Depends(get_db)):
    total = db.query(func.count(Provider.id)).scalar() or 0
    verified = db.query(func.count(Provider.id)).filter(Provider.validation_status=="VERIFIED").scalar() or 0
    flagged = db.query(func.count(Provider.id)).filter(Provider.validation_status=="FLAGGED").scalar() or 0
    invalid = db.query(func.count(Provider.id)).filter(Provider.validation_status=="INVALID").scalar() or 0
    avg_conf = db.query(func.avg(Provider.confidence_score)).scalar() or 0.0
    return {
        "total": total, "verified": verified, "flagged": flagged, "invalid": invalid,
        "avg_confidence": round(float(avg_conf), 2)
    }
