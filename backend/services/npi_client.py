import requests
from typing import Optional, Dict, Any
from ..config import settings
from ..utils.logger import log

def search_by_name(name: str, state: Optional[str]) -> Optional[Dict[str, Any]]:
    if settings.USE_MOCKS:
        # deterministic mock for demo
        parts = name.split()
        return {
            "number": "1043312345",
            "basic": {"first_name": parts[0], "last_name": parts[-1], "last_updated": "2025-01-12"},
            "addresses": [{
                "address_purpose": "LOCATION",
                "address_1": "123 MAIN ST",
                "city": "SAN FRANCISCO",
                "state": (state or "CA"),
                "postal_code": "94105",
                "telephone_number": "415-555-6622"
            }],
            "taxonomies": [{"desc": "Internal Medicine", "primary": True}]
        }

    params = {
        "version": "2.1",
        "limit": 1
    }
    # best effort split
    tokens = name.split()
    if len(tokens) >= 2:
        params["first_name"] = tokens[0]
        params["last_name"]  = tokens[-1]
    if state:
        params["state"] = state.upper()

    r = requests.get(settings.NPI_BASE_URL, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    if data.get("result_count", 0) < 1:
        return None
    return data["results"][0]

def search_by_npi(npi: str) -> Optional[Dict[str, Any]]:
    if settings.USE_MOCKS:
        return {
            "number": npi,
            "basic": {"first_name": "Alice", "last_name": "Monroe", "last_updated": "2025-01-12"},
            "addresses": [{
                "address_purpose": "LOCATION",
                "address_1": "221 BAKER ST",
                "city": "SAN FRANCISCO",
                "state": "CA",
                "postal_code": "94105",
                "telephone_number": "415-555-6622"
            }],
            "taxonomies": [{"desc": "Dermatology", "primary": True}]
        }
    r = requests.get(settings.NPI_BASE_URL, params={"number": npi, "version": "2.1"}, timeout=15)
    r.raise_for_status()
    data = r.json()
    if data.get("result_count", 0) < 1:
        return None
    return data["results"][0]
