import asyncio
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.database import Course, File as FileModel
from app.core.config import settings
from app.api.routes.auth import get_current_user
from app.processing.document_processor import SUPPORTED_DOCUMENT_FORMATS
from app.processing.image_processor import SUPPORTED_IMAGE_FORMATS

router = APIRouter()

MAX_UPLOAD = 100 * 1024 * 1024
UPLOAD_CHUNK_SIZE = 1024 * 1024


def _sanitize_filename(filename: Optional[str]) -> str:
    """Keep a display name while removing path components and control chars."""
    normalized = (filename or "").replace("\\", "/")
    basename = Path(normalized).name
    safe_name = "".join(char for char in basename if char.isprintable()).strip(" .")
    if len(safe_name) > 512:
        suffix = Path(safe_name).suffix
        safe_name = safe_name[: 512 - len(suffix)] + suffix
    return safe_name

def _file_type(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext == '.pdf': return 'pdf'
    if ext in SUPPORTED_IMAGE_FORMATS: return 'image'
    if ext in SUPPORTED_DOCUMENT_FORMATS: return 'text'
    return 'unknown'


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    course_id: str = Form(...),
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a local file and associate it with a course.
    Saves to local storage and creates a File record in the database.
    """
    fname = _sanitize_filename(file.filename)
    if not fname:
        raise HTTPException(status_code=400, detail="A valid filename is required.")

    ftype = _file_type(fname)
    if ftype == "unknown":
        raise HTTPException(status_code=415, detail="This file type is not supported.")

    course_result = await db.execute(
        select(Course).where(Course.id == course_id, Course.user_id == user.id)
    )
    if not course_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Course not found.")
    
    # Ensure user upload directory exists
    user_dir = Path(settings.UPLOAD_DIR) / user.id
    user_dir.mkdir(parents=True, exist_ok=True)
    
    # User-provided names are never used as filesystem paths.
    unique_filename = f"{uuid.uuid4()}{Path(fname).suffix.lower()}"
    local_path = user_dir / unique_filename

    file_size = 0
    try:
        with local_path.open("wb") as destination:
            while chunk := await file.read(UPLOAD_CHUNK_SIZE):
                file_size += len(chunk)
                if file_size > MAX_UPLOAD:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Max: {MAX_UPLOAD // 1024 // 1024}MB",
                    )
                await asyncio.to_thread(destination.write, chunk)
        if file_size == 0:
            raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    except Exception:
        await asyncio.to_thread(local_path.unlink, missing_ok=True)
        raise
    
    # Create DB record
    new_file = FileModel(
        id=str(uuid.uuid4()),
        user_id=user.id,
        course_id=course_id,
        drive_name=fname,
        mime_type=file.content_type,
        local_path=str(local_path),
        file_size=file_size,
        detected_type=ftype,
        processing_status="pending"
    )
    
    try:
        db.add(new_file)
        await db.commit()
        await db.refresh(new_file)
    except Exception:
        await db.rollback()
        await asyncio.to_thread(local_path.unlink, missing_ok=True)
        raise
    
    return {
        "status": "success",
        "file_id": new_file.id,
        "file_name": fname,
        "processing_status": "pending"
    }


@router.get("/supported-formats")
async def get_supported_formats(_user=Depends(get_current_user)):
    return {
        "pdf": [".pdf"],
        "image": sorted(SUPPORTED_IMAGE_FORMATS),
        "document": sorted(SUPPORTED_DOCUMENT_FORMATS),
    }
