from typing import Dict, Any
from ..services.license_client import verify_license

def enrich_with_license(row: Dict[str, Any]) -> Dict[str, Any]:
    return verify_license(row.get("license_number"), row.get("license_state"))
