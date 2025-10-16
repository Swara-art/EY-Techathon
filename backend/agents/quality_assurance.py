from typing import Dict, Any
from ..services.scoring import compute_confidence

def qa_score(input_row: Dict[str, Any], npi_row: Dict[str, Any] | None, scrape_row: Dict[str, Any] | None, license_row: Dict[str, Any]):
    return compute_confidence(input_row, npi_row, scrape_row, license_row)
