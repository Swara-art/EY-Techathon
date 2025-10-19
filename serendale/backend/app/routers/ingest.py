# ingest.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from pathlib import Path
from ..db import get_collection
import aiofiles
import os

router = APIRouter(
    prefix="/ingest",
    tags=["Ingest"]
)

# Pantry location
UPLOAD_DIR = Path(__file__).parent.parent / "uploads"

@router.post("/providers")
async def upload_provider_file(request: Request, file: UploadFile = File(...)):
    """
    1. Receives a file from the user (customer order)
    2. Puts it in the right folder (pantry shelf based on type)
    3. Records the file info in MongoDB (inventory book)
    """

    # 1️⃣ Determine file type (like checking ingredient type)
    file_type = Path(file.filename).suffix.lstrip(".")
    if not file_type:
        file_type = (file.content_type.split("/")[-1]) if file.content_type else "unknown"

    # 2️⃣ Ensure folder exists for that type (create shelf if missing)
    folder = UPLOAD_DIR / file_type
    folder.mkdir(parents=True, exist_ok=True)

    # 3️⃣ Save the file asynchronously (put ingredient on shelf carefully)
    file_path = folder / file.filename
    try:
        async with aiofiles.open(file_path, "wb") as out_file:
            while True:
                chunk = await file.read(1024 * 64)  # read in chunks
                if not chunk:
                    break
                await out_file.write(chunk)
    except Exception as e:
        await file.close()
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")
    await file.close()

    # 4️⃣ Insert metadata into MongoDB (write in inventory book)
    try:
        collection = get_collection(request)  # pass request as your function expects
        doc = {
            "filename": file.filename,
            "filepath": str(file_path),
            "filetype": file_type
        }
        print("Inserting doc:", doc)
        result = await collection.insert_one(doc)
        print("Inserted ID:", result.inserted_id)
    except Exception as e:
        # If DB fails, remove the saved file (undo inventory if we can't record it)
        try:
            os.remove(file_path)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Failed to insert document: {e}")

    # 5️⃣ Return success message to user
    return {
        "message": "File uploaded successfully",
        "id": str(result.inserted_id),
        "filename": file.filename,
        "path": str(file_path),
        "type": file_type
    }
