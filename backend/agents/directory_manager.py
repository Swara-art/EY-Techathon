from sqlalchemy.orm import Session
from ..models import Provider, ValidationLog
import json
from typing import Dict, Any

def persist_validation(db: Session, provider: Provider, results: Dict[str, Any], score: float):
    provider.confidence_score = score
    provider.validation_status = "VERIFIED" if score >= 0.8 else ("FLAGGED" if score >= 0.5 else "INVALID")
    db.add(ValidationLog(
        provider_id=provider.id,
        raw_sources=json.dumps(results),
        summary=f"status={provider.validation_status}, score={score}"
    ))
    db.commit()
    db.refresh(provider)
    return provider
