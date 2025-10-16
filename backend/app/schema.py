from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class ProviderIn(BaseModel):
    npi: Optional[str] = None
    name: str
    specialty: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    license_number: Optional[str] = None
    license_state: Optional[str] = None

class ProviderOut(ProviderIn):
    id: int
    confidence_score: float
    validation_status: str

    class Config:
        from_attributes = True

class BatchRequest(BaseModel):
    limit: int = Field(default=200, le=1000)
    states: Optional[list[str]] = None
    status_filter: Optional[list[str]] = None  # e.g., ["PENDING","FLAGGED"]

class ValidationResult(BaseModel):
    provider_id: int
    status: str
    confidence_score: float
    details: Dict[str, Any] = {}
