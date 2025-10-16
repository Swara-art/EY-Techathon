def normalize(s: str | None) -> str:
    return (s or "").strip().lower()

def compute_confidence(input_row: dict, npi_row: dict, scrape_row: dict, license_row: dict) -> float:
    score = 0.0

    # NPI identity & specialty
    if npi_row:
        score += 0.2  # existence
        if normalize(input_row.get("name")).split(" ")[0:1] == []:
            pass
        else:
            score += 0.1
        if normalize(input_row.get("specialty")) in normalize(npi_row.get("specialty", "")):
            score += 0.15

    # Contact (phone/address) match between input and either NPI or scraper
    for src in (npi_row, scrape_row):
        if not src: continue
        if normalize(input_row.get("phone")) and normalize(src.get("phone")) == normalize(input_row.get("phone")):
            score += 0.15
            break

    # Address city/state alignment
    in_state = normalize(input_row.get("state"))
    src_state = normalize(npi_row.get("state") if npi_row else "") or normalize(scrape_row.get("state") if scrape_row else "")
    if in_state and src_state and in_state == src_state:
        score += 0.1

    # License status
    if license_row and license_row.get("status") == "ACTIVE":
        score += 0.2

    return round(min(score, 1.0), 2)
