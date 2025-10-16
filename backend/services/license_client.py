from typing import Optional, Dict, Any
from ..config import settings

# Hackathon-friendly: mock license verifier + easy extension points for real scrapers/APIs
def verify_license(license_number: Optional[str], state: Optional[str]) -> Dict[str, Any]:
    if not license_number or not state:
        return {"status": "UNKNOWN", "expiry": None, "source": None}
    if settings.USE_MOCKS:
        return {"status": "ACTIVE", "expiry": "2026-04-15", "source": f"{state.upper()}_BOARD_MOCK"}
    # TODO: implement real scrapers per-state or integrate paid APIs if available
    return {"status": "UNKNOWN", "expiry": None, "source": None}
