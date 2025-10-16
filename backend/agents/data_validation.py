from typing import Dict, Any, Optional
from ..services import npi_client, web_scraper

def validate_provider_row(row: Dict[str, Any]) -> Dict[str, Any]:
    # NPI lookup
    npi_res = npi_client.search_by_npi(row["npi"]) if row.get("npi") else npi_client.search_by_name(row["name"], row.get("state"))
    mapped_npi = None
    if npi_res:
        addr = npi_res["addresses"][0]
        mapped_npi = {
            "npi": str(npi_res.get("number")),
            "name": f"{npi_res['basic'].get('first_name','')} {npi_res['basic'].get('last_name','')}".strip(),
            "phone": addr.get("telephone_number"),
            "address": f"{addr.get('address_1')}, {addr.get('city')}, {addr.get('state')}",
            "state": addr.get("state"),
            "specialty": npi_res["taxonomies"][0].get("desc") if npi_res.get("taxonomies") else None,
            "last_updated": npi_res["basic"].get("last_updated"),
        }

    # Scrape practice site / public directory
    scrape_res = web_scraper.scrape_practice_contact(row["name"], row.get("city"), row.get("state"))

    return {"npi": mapped_npi, "scrape": scrape_res}
