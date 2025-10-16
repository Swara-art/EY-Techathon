from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.sql import func
from .database import Base

class Provider(Base):
    __tablename__ = "providers"
    id = Column(Integer, primary_key=True, index=True)
    npi = Column(String, index=True)
    name = Column(String, index=True)
    specialty = Column(String)
    phone = Column(String)
    address = Column(String)
    city = Column(String)
    state = Column(String(2))
    postal_code = Column(String)
    license_number = Column(String)
    license_state = Column(String(2))
    license_status = Column(String)
    license_expiry = Column(String)
    confidence_score = Column(Float, default=0.0)
    validation_status = Column(String, default="PENDING")  # PENDING | VERIFIED | FLAGGED | INVALID
    last_validated_at = Column(DateTime, server_default=func.now())

class ValidationLog(Base):
    __tablename__ = "validation_logs"
    id = Column(Integer, primary_key=True)
    provider_id = Column(Integer, index=True)
    raw_sources = Column(Text)  # json string of sources per field
    summary = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
