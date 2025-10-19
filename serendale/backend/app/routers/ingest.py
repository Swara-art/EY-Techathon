# backend/app/routers/ingest.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
from ..db import get_collection
import aiofiles, os
import os, re, json, time, math, random, string, datetime as dt, textwrap
from pathlib import Path
from dataclasses import dataclass
import pandas as pd
import numpy as np
import requests, httpx
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from rapidfuzz import fuzz, process
from dateutil import parser as dateparser
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split
import kagglehub
import re, time, json, math, datetime, random
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential
from fake_useragent import UserAgent
from io import BytesIO
router = APIRouter(prefix="/ingest", tags=["Ingest"])

# ✅ Point to backend/app/uploads (routers -> app -> uploads)
UPLOAD_ROOT = (Path(__file__).resolve().parents[1] / "uploads").resolve()
UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
def val(df):   
    BASE_DIR = Path(".")
    OUT_DIR = BASE_DIR / "provider_pipeline_outputs"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # If you have a Kaggle CSV, set this path.
    # Expected useful columns (best-effort mapping): name, npi, phone, address, specialty, license_state, license_number, website, email
    INPUT_CSV_PATH = "healthcare_providers.csv" 
    # === Row-by-row cleaner + validator (with canonicalization patch + validators + anomaly detection) ===
    # Precondition: `df` exists (pandas DataFrame). This cell will safely update df in-place.
    # Configure:
    SIMULATE = False           # True -> skip NPI + scraping (useful for offline tests)
    APPLY_AUTO_CHANGES = True  # If True, apply candidate values when action == "auto_apply"
    OUT_DIR = "outputs"
    MAX_ROWS = None            # None => process all; or set an int to limit during dev
    RATE_LIMIT_SECONDS = 0.12  # polite pause between external calls
    AUTO_THRESHOLD = 0.85
    STAGE_THRESHOLD = 0.60
    
    
    Path(OUT_DIR).mkdir(parents=True, exist_ok=True)
    ua = UserAgent()
    random.seed(42)
    
    # ---- Utilities ----
    def now_iso_z():
        return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
    
    def clean_spaces(s):
        return re.sub(r"\s+", " ", str(s)).strip() if pd.notna(s) else ""
    
    def normalize_phone(phone):
        p = clean_spaces(phone)
        if not p: return ""
        s = re.sub(r"[^\d\+]", "", p)
        if not s: return ""
        if not s.startswith("+"):
            digits = re.sub(r"\D", "", s)
            if len(digits) == 10:
                return "+91" + digits if digits.startswith("9") else "+1" + digits
            return "+" + digits
        return s
    
    def normalize_address(addr):
        if not addr: return ""
        return clean_spaces(str(addr).replace("\n", ", "))
    
    def split_name(fullname):
        n = clean_spaces(fullname or "")
        n = re.sub(r"^(dr\.?\s+)", "", n, flags=re.I)
        toks = n.split()
        if len(toks) >= 2:
            return toks[0], toks[-1]
        return (toks[0], "") if toks else ("", "")
    
    def clamp01(x): return max(0.0, min(1.0, float(x)))
    
    # ---- External helpers (NPI + scraping) ----
    # NPI lookup with retries
    class SoftError(Exception): pass
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=6), reraise=True)
    def npi_lookup(number=None, first_name=None, last_name=None, timeout=6):
        params = {"version":"2.1"}
        if number: params["number"]=number
        if first_name: params["first_name"]=first_name
        if last_name: params["last_name"]=last_name
        r = requests.get("https://npiregistry.cms.hhs.gov/api/", params=params, timeout=timeout)
        if r.status_code >= 500: raise SoftError(f"NPI 5xx {r.status_code}")
        r.raise_for_status()
        return r.json()
    
    def scrape_contact(url, timeout=8):
        if not url or not isinstance(url, str) or not url.strip(): return {}
        headers = {"User-Agent": ua.random}
        try:
            r = requests.get(url, headers=headers, timeout=timeout)
            if r.status_code != 200: return {}
            soup = BeautifulSoup(r.text, "html.parser")
            tel = soup.select_one("a[href^='tel:']")
            phone = tel.get_text(strip=True) if tel else None
            if not phone:
                txt = soup.get_text(" ", strip=True)
                m = re.search(r"(\+?\d[\d\-\s\(\)]{7,}\d)", txt)
                phone = m.group(1) if m else None
            addr_tag = soup.find("address")
            address = addr_tag.get_text(" ", strip=True) if addr_tag else None
            if not address:
                cand = soup.find(class_=re.compile("address|location|contact", re.I))
                address = cand.get_text(" ", strip=True) if cand else None
            return {"phone": normalize_phone(phone) if phone else "", "address": normalize_address(address) if address else ""}
        except Exception:
            return {}
    
    def simple_state_board_check(license_state, license_number):
        if not license_state or not license_number:
            return {"status":"Unknown","source":"adapter"}
        if re.match(rf"^{re.escape(license_state)}-[A-Z0-9]{{6}}$", str(license_number)):
            return {"status":"Active","source":"adapter"}
        return {"status":"NotFound","source":"adapter"}
    
    # ---- Scoring / decision rules ----
    def score_field(evidence):
        """evidence: list of (source_label, value, reliability:0..1)"""
        if not evidence: return 0.0, ""
        vals = [(s, (v or "").strip(), r) for (s,v,r) in evidence]
        weights = {}
        for _,v,r in vals:
            weights.setdefault(v, 0.0)
            weights[v] += r
        candidate = max(weights.items(), key=lambda kv: kv[1])[0]
        agree = sum(1 for (_,v,_) in vals if v == candidate) / len(vals)
        max_rel = max(r for (_,v,r) in vals if v == candidate) if vals else 0.0
        combined = clamp01(0.5*max_rel + 0.35*agree + 0.15*min(1.0, weights[candidate]/len(vals)))
        return round(combined,3), (candidate if candidate!="" else "")
    
    def decide_action(conf):
        if conf >= AUTO_THRESHOLD: return "auto_apply"
        if conf >= STAGE_THRESHOLD: return "stage_review"
        return "flag_for_manual_review"
    
    # ---- Per-row processing function ----
    def process_provider_row(row, simulate=SIMULATE):
        """
        row: pandas Series representing a row (clean/normalized input)
        returns: dict with candidate fields, confidences, actions, suspicious, last_validated_at
        """
        name = clean_spaces(row.get("name",""))
        npi = clean_spaces(str(row.get("npi","")))
        phone_input = normalize_phone(row.get("phone",""))
        addr_input  = normalize_address(row.get("address",""))
        spec_input  = clean_spaces(row.get("specialty",""))
        lic_state   = clean_spaces(row.get("license_state",""))
        lic_num     = clean_spaces(row.get("license_number",""))
        website     = clean_spaces(row.get("website",""))
    
        # Evidence lists
        ev_phone, ev_addr, ev_spec, ev_lic = [], [], [], []
    
        # input evidence (low reliability)
        if phone_input: ev_phone.append(("input", phone_input, 0.35))
        if addr_input: ev_addr.append(("input", addr_input, 0.35))
        if spec_input: ev_spec.append(("input", spec_input, 0.35))
        if lic_num: ev_lic.append(("input", lic_num, 0.35))
    
        # NPI enrichment
        npi_payload = {}
        if not simulate:
            try:
                if npi:
                    npi_payload = npi_lookup(number=npi)
                else:
                    fn, ln = split_name(name)
                    if fn or ln:
                        npi_payload = npi_lookup(first_name=fn or None, last_name=ln or None)
                time.sleep(RATE_LIMIT_SECONDS)
            except Exception:
                npi_payload = {}
        # parse NPI results
        try:
            results = npi_payload.get("results") if isinstance(npi_payload, dict) else []
            if results:
                r0 = results[0]
                tax = r0.get("taxonomies") or []
                npi_spec = tax[0].get("desc","") if tax else ""
                addrs = r0.get("addresses") or []
                locs = [a for a in addrs if a.get("address_purpose")=="LOCATION"] or addrs
                if locs:
                    a0 = locs[0]
                    npi_phone = a0.get("telephone_number","") or a0.get("phone_number","") or ""
                    npi_addr = ", ".join([p for p in [a0.get("address_1",""), a0.get("address_2",""), a0.get("city",""), a0.get("state",""), a0.get("postal_code","")] if p])
                    if npi_phone: ev_phone.append(("npi", normalize_phone(npi_phone), 0.92))
                    if npi_addr: ev_addr.append(("npi", normalize_address(npi_addr), 0.92))
                    if npi_spec: ev_spec.append(("npi", npi_spec, 0.88))
        except Exception:
            pass
    
        # Website scrape
        if website and not simulate:
            try:
                scraped = scrape_contact(website)
                if scraped.get("phone"): ev_phone.append(("website", scraped.get("phone"), 0.80))
                if scraped.get("address"): ev_addr.append(("website", scraped.get("address"), 0.80))
                time.sleep(RATE_LIMIT_SECONDS)
            except Exception:
                pass
    
        # License check
        lic_result = simple_state_board_check(lic_state, lic_num)
        ev_lic.append(("state_board", lic_result.get("status","Unknown"), 0.75 if lic_result.get("status")=="Active" else 0.35))
    
        # Score fields
        phone_conf, phone_cand = score_field(ev_phone)
        addr_conf, addr_cand   = score_field(ev_addr)
        spec_conf, spec_cand   = score_field(ev_spec)
        lic_conf, lic_cand     = score_field(ev_lic)
    
        phone_action = decide_action(phone_conf)
        addr_action  = decide_action(addr_conf)
        spec_action  = decide_action(spec_conf)
        lic_action   = decide_action(lic_conf)
    
        overall_conf = round((phone_conf + addr_conf + spec_conf + lic_conf) / 4.0, 3)
    
        # Suspicious heuristics
        suspicious = False
        suspicious_reasons = []
        if lic_cand in [None, "", "NotFound"] or lic_conf < 0.5:
            suspicious = True
            suspicious_reasons.append("license_missing_or_low_confidence")
        if not npi and (phone_action != "auto_apply" or addr_action != "auto_apply"):
            suspicious = True
            suspicious_reasons.append("missing_npi_unconfirmed_contact")
    
        return {
            "phone_candidate": phone_cand, "phone_confidence": phone_conf, "phone_action": phone_action,
            "address_candidate": addr_cand, "address_confidence": addr_conf, "address_action": addr_action,
            "specialty_candidate": spec_cand, "specialty_confidence": spec_conf, "specialty_action": spec_action,
            "license_candidate": lic_cand, "license_confidence": lic_conf, "license_action": lic_action,
            "overall_confidence": overall_conf,
            "suspicious": suspicious,
            "suspicious_reasons": ";".join(suspicious_reasons),
            "last_validated_at": now_iso_z()
        }
    
    # ---- Main safe loop: update df in-place using .loc ----
    if "df" not in globals():
        raise RuntimeError("DataFrame variable `df` not found in the notebook. Load the dataset into `df` and re-run.")
    
    # Make a safe copy (avoid modifying a view)
    df = df.copy(deep=True)
    
    # Add stable original index column for traceability (keeps original index values)
    df["_orig_index"] = df.index
    
    # -------------------------- NEW PATCH: canonicalize raw columns --------------------------
    # Map raw Kaggle headers into canonical short fields and normalize NPI/ZIP types
    RAW_NPI = "National Provider Identifier"
    RAW_ZIP = "Zip Code of the Provider"
    RAW_STATE = "State Code of the Provider"
    RAW_STREET = "Street Address 1 of the Provider"
    RAW_CRED = "Credentials of the Provider"
    RAW_FIRST = "First Name of the Provider"
    RAW_LAST = "Last Name/Organization Name of the Provider"
    
    # keep raw copies (audit)
    if RAW_NPI in df.columns:
        df.loc[:, "npi_raw"] = df[RAW_NPI].astype(str).fillna("")
    else:
        df.loc[:, "npi_raw"] = df.get("npi_raw", "").astype(str).fillna("")
    
    if RAW_ZIP in df.columns:
        df.loc[:, "zip_raw"] = df[RAW_ZIP].astype(str).fillna("")
    else:
        df.loc[:, "zip_raw"] = df.get("zip_raw", "").astype(str).fillna("")
    
    # helper to extract first N digits from any string/float
    def extract_first_digits(s, n=10):
        if pd.isna(s): return ""
        s = str(s).replace(",", "").strip()
        # find sequences of digits length >= n; return leftmost n
        m = re.search(r"(\d{%d,})" % n, s)
        if m:
            return m.group(1)[:n]
        digits = re.sub(r"\D", "", s)
        return digits[:n] if len(digits) >= n else digits
    
    # populate canonical 'npi' (10 digits) and 'zip5' (first 5 digits)
    df.loc[:, "npi"] = df["npi_raw"].apply(lambda x: extract_first_digits(x, 10))
    df.loc[:, "zip5"] = df["zip_raw"].astype(str).apply(lambda s: (re.search(r"(\d{5})", s).group(1) if re.search(r"(\d{5})", s) else ""))
    
    # map state, street and credentials to canonical fields (non-destructively)
    if RAW_STATE in df.columns:
        df.loc[:, "state"] = df[RAW_STATE].astype(str).str.upper().fillna("")
    else:
        df.loc[:, "state"] = df.get("state","").astype(str).str.upper().fillna("")
    
    if RAW_STREET in df.columns:
        df.loc[:, "address"] = df[RAW_STREET].astype(str).fillna("")
    else:
        # keep existing if any
        df.loc[:, "address"] = df.get("address","").astype(str).fillna("")
    
    if RAW_CRED in df.columns:
        df.loc[:, "credentials"] = df[RAW_CRED].astype(str).fillna("")
    else:
        df.loc[:, "credentials"] = df.get("credentials","").astype(str).fillna("")
    
    # if a 'name' column doesn't exist or is empty, build one from first+last
    if "name" not in df.columns or df["name"].isnull().all() or df["name"].astype(str).str.strip().eq("").all():
        if RAW_FIRST in df.columns or RAW_LAST in df.columns:
            df.loc[:, "name"] = (df.get(RAW_FIRST, "").astype(str).fillna("").str.strip() + " " + df.get(RAW_LAST, "").astype(str).fillna("").str.strip()).str.strip()
        else:
            df.loc[:, "name"] = df.get("name","").astype(str).fillna("")
    
    # ---------------------------------------------------------------------------------------
    
    # Ensure canonical columns exist and use .loc to avoid SettingWithCopyWarning
    canonical = ["provider_id","name","npi","phone","address","specialty","license_state","license_number","website","email"]
    for c in canonical:
        if c not in df.columns:
            df.loc[:, c] = ""
    
    # Normalize inputs (in-place, safe .loc)
    df.loc[:, "name"] = df["name"].apply(clean_spaces)
    df.loc[:, "phone"] = df["phone"].apply(normalize_phone)
    df.loc[:, "address"] = df["address"].apply(normalize_address)
    df.loc[:, "specialty"] = df["specialty"].apply(clean_spaces)
    df.loc[:, "npi"] = df["npi"].astype(str).apply(clean_spaces)
    
    # === B: Add explicit rule-based validators (run AFTER normalization, BEFORE loop) ===
    # This block creates npi_valid, zip_valid, zip5, state_valid, credential_present, address_present
    zip_col = "Zip Code of the Provider"
    state_col = "State Code of the Provider"
    cred_col = "Credentials of the Provider"
    street_col = "Street Address 1 of the Provider"
    
    # NPI format boolean (10 digits) -- now uses canonical df['npi']
    df.loc[:, "npi_valid"] = df["npi"].astype(str).str.fullmatch(r"\d{10}").fillna(False)
    
    # ZIP (5 digits) — accept 12345 or 12345-6789; prefer canonical zip5 computed above
    df.loc[:, "zip_valid"] = df.get("zip5", "").astype(str).str.fullmatch(r"\d{5}").fillna(False)
    # keep zip_raw if exists for audit
    df.loc[:, "zip_raw"] = df.get("zip_raw", "").astype(str).fillna("")
    
    # State code (2 alpha) — uppercase and validate (uses canonical df['state'])
    df.loc[:, "state_valid"] = df.get("state", "").astype(str).str.fullmatch(r"[A-Z]{2}").fillna(False)
    
    # credential presence (use canonical credentials)
    df.loc[:, "credential_present"] = df.get("credentials", "").astype(str).str.strip().astype(bool)
    
    # address presence (primary street address) (uses canonical 'address')
    df.loc[:, "address_present"] = df.get("address", "").astype(str).str.strip().astype(bool)
    
    # Optional: quick summary to check counts (print once)
    try:
        print("Validators summary: npi_valid:", int(df["npi_valid"].sum()), "zip_valid:", int(df["zip_valid"].sum()), "state_valid:", int(df["state_valid"].sum()), "address_present:", int(df["address_present"].sum()))
    except Exception:
        pass
    
    # Optional row limit
    if MAX_ROWS is not None:
        process_index_list = df.index.tolist()[:MAX_ROWS]
    else:
        process_index_list = df.index.tolist()
    
    # Prepare audit_log list (optional, empty)
    audit_log = []
    
    # Iterate row-by-row and update via .loc
    print("Starting validation loop over", len(process_index_list), "rows; SIMULATE =", SIMULATE)
    for i, idx in enumerate(process_index_list, 1):
        try:
            row = df.loc[idx]  # series snapshot
            res = process_provider_row(row, simulate=SIMULATE)
        except Exception as e:
            # safe fallback for a row failure
            res = {
                "phone_candidate":"", "phone_confidence":0.0, "phone_action":"flag_for_manual_review",
                "address_candidate":"", "address_confidence":0.0, "address_action":"flag_for_manual_review",
                "specialty_candidate":"", "specialty_confidence":0.0, "specialty_action":"flag_for_manual_review",
                "license_candidate":"", "license_confidence":0.0, "license_action":"flag_for_manual_review",
                "overall_confidence":0.0, "suspicious":True, "suspicious_reasons":"processing_error",
                "last_validated_at": now_iso_z()
            }
    
        # Append minimal audit entry for this row (optional)
        audit_entry = {
            "_orig_index": idx,
            "provider_id": df.loc[idx].get("provider_id", None) if idx in df.index else None,
            "input_phone": df.loc[idx].get("phone", None),
            "input_address": df.loc[idx].get("address", None),
            "phone_candidate": res.get("phone_candidate"),
            "phone_confidence": res.get("phone_confidence"),
            "address_confidence": res.get("address_confidence"),
            "overall_confidence": res.get("overall_confidence"),
            "suspicious": res.get("suspicious"),
            "suspicious_reasons": res.get("suspicious_reasons"),
            "last_validated_at": res.get("last_validated_at")
        }
        audit_log.append(audit_entry)
    
        # Assign back to df row using .loc (safe)
        for k,v in res.items():
            df.loc[idx, k] = v
    
        # If apply auto changes, write them back to main columns
        if APPLY_AUTO_CHANGES:
            if df.loc[idx, "phone_action"] == "auto_apply" and df.loc[idx, "phone_candidate"]:
                df.loc[idx, "phone"] = df.loc[idx, "phone_candidate"]
            if df.loc[idx, "address_action"] == "auto_apply" and df.loc[idx, "address_candidate"]:
                df.loc[idx, "address"] = df.loc[idx, "address_candidate"]
            if df.loc[idx, "specialty_action"] == "auto_apply" and df.loc[idx, "specialty_candidate"]:
                df.loc[idx, "specialty"] = df.loc[idx, "specialty_candidate"]
            if df.loc[idx, "license_action"] == "auto_apply" and df.loc[idx, "license_candidate"]:
                df.loc[idx, "license_number"] = df.loc[idx, "license_candidate"]
    
        # small progress print every 200 rows
        if i % 200 == 0:
            print(f"Processed {i}/{len(process_index_list)} rows...")
    
    # ---- C: Anomaly detection (run AFTER loop) ----
    # Choose numeric columns available in the dataset
    numeric_candidates = [
        "Number of Services",
        "Number of Medicare Beneficiaries",
        "Number of Distinct Medicare Beneficiary/Per Day Services",
        "Average Medicare Allowed Amount",
        "Average Submitted Charge Amount",
        "Average Medicare Payment Amount",
        "Average Medicare Standardized Amount"
    ]
    num_cols = [c for c in numeric_candidates if c in df.columns]
    
    if num_cols:
        X = df[num_cols].apply(pd.to_numeric, errors="coerce").fillna(0.0)
        try:
            iso = IsolationForest(n_estimators=200, contamination=0.05, random_state=42)
            iso.fit(X)
            scores_raw = iso.decision_function(X)   # higher => less anomalous
            mn, mx = float(scores_raw.min()), float(scores_raw.max())
            if mx - mn > 0:
                df.loc[:, "iso_score"] = ((scores_raw - mn) / (mx - mn)).round(3)
            else:
                df.loc[:, "iso_score"] = 1.0
            # anomaly_flag (tunable)
            ANOMALY_THRESHOLD = 0.25
            df.loc[:, "anomaly_flag"] = df["iso_score"] < ANOMALY_THRESHOLD
        except Exception as e:
            # If IsolationForest fails for any reason, fallback to no anomalies
            df.loc[:, "iso_score"] = 1.0
            df.loc[:, "anomaly_flag"] = False
    else:
        df.loc[:, "iso_score"] = 1.0
        df.loc[:, "anomaly_flag"] = False
    
    # Penalize overall_confidence for anomalies (tunable)
    ANOMALY_PENALTY = 0.25
    if "overall_confidence" in df.columns:
        df.loc[:, "overall_confidence"] = (df["overall_confidence"].astype(float) - df["anomaly_flag"].astype(float)*ANOMALY_PENALTY).clip(0,1).round(3)
    else:
        df.loc[:, "overall_confidence"] = 0.0
    
    # Compute a single provider-level action if you want (optional)
    def decide_row_action(overall_conf):
        if overall_conf >= AUTO_THRESHOLD: return "Confident"
        if overall_conf >= STAGE_THRESHOLD: return "Average"
        return "Need Manual Review"
    df.loc[:, "row_action"] = df["overall_confidence"].astype(float).apply(decide_row_action)
    
    # Recompute priority score after anomaly penalty
    df.loc[:, "priority_score"] = (1 - df["overall_confidence"].astype(float)) + df["suspicious"].astype(int) * 0.5
    
    # Save audit log (jsonl) and outputs
    audit_path = Path(OUT_DIR) / "audit_log.jsonl"
    with open(audit_path, "w", encoding="utf8") as fh:
        for rec in audit_log:
            fh.write(json.dumps(rec) + "\n")
    
    out_updated = Path(OUT_DIR) / "updated_providers_with_validation.csv"
    out_priority = Path(OUT_DIR) / "prioritized_manual_review.csv"
    out_emails = Path(OUT_DIR) / "provider_emails.csv"
    
    df.to_csv(out_updated, index=False)
    df.sort_values("priority_score", ascending=False).to_csv(out_priority, index=False)
    
    # Build email drafts for staged/auto changes
    emails = []
    for _, row in df.iterrows():
        ch = []
        # compare candidate -> current (note: if APPLY_AUTO_CHANGES was True, phone/address may already be updated)
        if row.get("phone_action") in ("auto_apply","stage_review") and row.get("phone_candidate") and row.get("phone_candidate") != row.get("phone"):
            ch.append(f"Phone: {row.get('phone')} -> {row.get('phone_candidate')} (conf {row.get('phone_confidence')})")
        if row.get("address_action") in ("auto_apply","stage_review") and row.get("address_candidate") and row.get("address_candidate") != row.get("address"):
            ch.append(f"Address: {row.get('address')} -> {row.get('address_candidate')} (conf {row.get('address_confidence')})")
        if ch:
            emails.append({"provider_id": row.get("provider_id"), "to": row.get("email",""), "subject": f"Confirm updates for {row.get('name')}", "body": "\n".join(ch)})
    
    pd.DataFrame(emails).to_csv(out_emails, index=False)
    
    print("Validation pass complete.")
    print("Outputs:")
    print(" - Updated CSV:", out_updated)
    print(" - Priority queue:", out_priority)
    print(" - Email drafts:", out_emails)
    print(" - Audit log:", audit_path)
    df.to_csv('output.csv', index=False)
    
    
def _sanitize_filename(name: str) -> str:
    safe = "".join(c for c in name if c.isalnum() or c in ("-", "_", ".", " ")).strip()
    return safe or "file"

@router.post("/providers")
async def upload_provider_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename missing")

    original_name = _sanitize_filename(file.filename)
    stem = Path(original_name).stem or "file"  # folder name under uploads
    content_type = file.content_type or "application/octet-stream"
    contents = await file.read()              # bytes

    # backend/app/uploads/<stem>/<original_name>
    target_dir = (UPLOAD_ROOT / stem).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = (target_dir / original_name).resolve()

    # keep writes inside UPLOAD_ROOT only
    if UPLOAD_ROOT not in target_path.parents and UPLOAD_ROOT != target_path:
        raise HTTPException(status_code=400, detail="Invalid file path")

    # save file
    try:
        async with aiofiles.open(target_path, "wb") as out:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                await out.write(chunk)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")
    finally:
        await file.close()
    
    # store minimal metadata in Mongo
    try:
        collection = get_collection()  # no args
        rel_path = target_path.relative_to(UPLOAD_ROOT.parent).as_posix()  # backend/app/uploads/...
        doc = {
            "filename": original_name,
            "filepath": rel_path,      # e.g., backend/app/uploads/output/output.csv
            "filetype": content_type,  # MIME type
        }
        result = await collection.insert_one(doc)
        #validate code
             # Reset file pointer to start
        await file.seek(0)
        
        # Try UTF-8 first
        try:
                df = pd.read_csv(BytesIO(await file.read()))
        except UnicodeDecodeError:
                # If UTF-8 fails, try with latin-1
                await file.seek(0)
                df = pd.read_csv(BytesIO(await file.read()), encoding='latin-1')
            
            # Reset index to ensure _orig_index exists
        df = df.reset_index(drop=False).rename(columns={'index': '_orig_index'})
            
            # Pass DataFrame to validation function
        val(df)
        print("Validation completed successfully")
    except Exception as e:
        try: os.remove(target_path)
        except Exception: pass
        raise HTTPException(status_code=500, detail=f"Failed to insert document: {e}")

    return {
        "message": "File uploaded successfully",
        "id": str(result.inserted_id),
        "filename": original_name,
        "path": rel_path,
        "type": content_type
    }


