# app/routers/ingest.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from typing import AsyncGenerator, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import UpdateOne, InsertOne
import csv, io, json

router = APIRouter(prefix="/ingest", tags=["ingest"])

# Allowed columns (anything else is ignored safely)
ALLOWED_FIELDS = {
    "npi","name","specialty","phone","address","city","state","postal_code",
    "license_number","license_state"
}

BATCH_SIZE = 1000

def _normalize_row(r: dict) -> dict:
    out = {}
    for k, v in r.items():
        key = (k or "").strip().lower()
        if key in ALLOWED_FIELDS:
            if isinstance(v, str):
                out[key] = v.strip()
            else:
                out[key] = v
    # optional: basic coercions
    if "npi" in out and out["npi"] == "":
        out.pop("npi")
    return out

async def _csv_rows(file: UploadFile) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Stream CSV rows as dicts using TextIOWrapper without loading entire file into memory.
    """
    # reset pointer just in case
    await file.seek(0)
    text_stream = io.TextIOWrapper(file.file, encoding="utf-8", newline="")
    reader = csv.DictReader(text_stream)
    for row in reader:
        yield row

async def _json_docs(file: UploadFile) -> List[Dict[str, Any]]:
    """
    Accept both:
      - JSON array: [ {...}, {...} ]
      - NDJSON (one JSON object per line)
    """
    await file.seek(0)
    raw = await file.read()
    # try JSON array first
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return [data]
        if isinstance(data, list):
            return data
        raise ValueError("JSON is not an object or array")
    except Exception:
        # NDJSON fallback
        docs = []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            docs.append(json.loads(line))
        return docs

def _build_ops(docs: List[Dict[str, Any]]) -> List[Any]:
    """
    Convert normalized documents into bulk ops:
      - If 'npi' exists: UpdateOne(upsert)
      - Else: InsertOne
    """
    ops = []
    for d in docs:
        d = _normalize_row(d)
        if not d:
            continue
        npi = d.get("npi")
        if npi:
            ops.append(
                UpdateOne({"npi": npi}, {"$set": d}, upsert=True)
            )
        else:
            ops.append(InsertOne(d))
    return ops

async def _bulk_apply(coll: AsyncIOMotorCollection, ops: List[Any]) -> Dict[str, int]:
    """
    Run bulk_write and return a compact summary.
    """
    summary = {"inserted": 0, "upserted": 0, "modified": 0, "errors": 0}
    if not ops:
        return summary
    try:
        res = await coll.bulk_write(ops, ordered=False)
        summary["inserted"] = res.inserted_count or 0
        summary["modified"] = res.modified_count or 0
        # upserts length:
        summary["upserted"] = len(res.upserted_ids or {})
    except Exception:
        # If anything goes wrong at batch level, count as errors
        summary["errors"] = len(ops)
    return summary

def _merge_sum(a: Dict[str,int], b: Dict[str,int]) -> Dict[str,int]:
    return {
        "inserted": a["inserted"] + b["inserted"],
        "upserted": a["upserted"] + b["upserted"],
        "modified": a["modified"] + b["modified"],
        "errors": a["errors"] + b["errors"],
    }

@router.post("/providers")
async def ingest_providers(request: Request, file: UploadFile = File(...)):
    """
    Upload a CSV or JSON/NDJSON file and upsert into MongoDB.
    Upsert key: 'npi' (if present). Otherwise inserts as new doc.
    """
    content_type = (file.content_type or "").lower()

    if not any(t in content_type for t in ("csv", "json", "ndjson")):
        # fallback by filename
        name = (file.filename or "").lower()
        if not (name.endswith(".csv") or name.endswith(".json") or name.endswith(".ndjson")):
            raise HTTPException(status_code=400, detail="Please upload a CSV, JSON, or NDJSON file.")

    coll: AsyncIOMotorCollection = request.app.state.providers
    overall = {"inserted": 0, "upserted": 0, "modified": 0, "errors": 0}

    # CSV path (streaming)
    if "csv" in content_type or (file.filename or "").lower().endswith(".csv"):
        buffer: List[Dict[str, Any]] = []
        async for row in _csv_rows(file):
            buffer.append(row)
            if len(buffer) >= BATCH_SIZE:
                ops = _build_ops(buffer)
                summary = await _bulk_apply(coll, ops)
                overall = _merge_sum(overall, summary)
                buffer.clear()
        if buffer:
            ops = _build_ops(buffer)
            summary = await _bulk_apply(coll, ops)
            overall = _merge_sum(overall, summary)
        return {"status": "ok", "summary": overall}

    # JSON / NDJSON path (loads in memory once)
    try:
        docs = await _json_docs(file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON/NDJSON: {e}")

    # chunk them
    for i in range(0, len(docs), BATCH_SIZE):
        chunk = docs[i : i + BATCH_SIZE]
        ops = _build_ops(chunk)
        summary = await _bulk_apply(coll, ops)
        overall = _merge_sum(overall, summary)

    return {"status": "ok", "summary": overall}
