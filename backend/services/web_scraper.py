from typing import Optional, Dict
# Placeholders – in hackathon, keep it simple (regex/heuristics)
def scrape_practice_contact(name: str, city: Optional[str], state: Optional[str]) -> Dict[str, Optional[str]]:
    # In real impl, search site / Google / HCA/HealthSystem pages
    # Return best-effort phone/address discovered
    return {
        "phone": "415-555-6622",
        "address": "221 Baker Street, San Francisco, CA 94105"
    }
