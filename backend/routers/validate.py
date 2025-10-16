from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Provider
from ..schemas import BatchRequest, ValidationResult
from ..agents.data_validation import validate_provider_row
from ..agents.enrichment import enrich_with_license
from ..agents.quality_assurance import qa_score
from ..agents.directory_manager import persist_validation

router = APIRouter(prefix="/validate", tags=["validation"])

def _validate_one(db: Session, p: Provider) -> ValidationResult:
    input_row = {
        "npi": p.npi, "name": p.name, "specialty": p.specialty, "phone": p.phone,
        "address": p.address, "city": p.city, "state": p.state,
        "license_number": p.license_number, "license_state": p.license_state
    }
    dv = validate_provider_row(input_row)
    lic = enrich_with_license(input_row)
    score = qa_score(input_row, dv.get("npi"), dv.get("scrape"), lic)

    # Persist
    updated = persist_validation(db, p, {"npi": dv.get("npi"), "scrape": dv.get("scrape"), "license": lic}, score)
    return ValidationResult(provider_id=updated.id, status=updated.validation_status, confidence_score=updated.confidence_score)

@router.post("/batch", response_model=list[ValidationResult])
def batch_validate(req: BatchRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    q = db.query(Provider)
    if req.states:
        q = q.filter(Provider.state.in_(req.states))
    if req.status_filter:
        q = q.filter(Provider.validation_status.in_(req.status_filter))
    providers = q.limit(req.limit).all()

    results = []
    for p in providers:
        results.append(_validate_one(db, p))
    return results
