# backend/app/routers/ingest.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
from ..db import get_collection
import aiofiles, os

router = APIRouter(prefix="/ingest", tags=["Ingest"])

# ✅ Point to backend/app/uploads (routers -> app -> uploads)
UPLOAD_ROOT = (Path(__file__).resolve().parents[1] / "uploads").resolve()
UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)

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


