from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from database.models import UploadedFile, Session as DBSession
from database.config import get_db
from backend.services.auth import get_current_user
from backend.services.file_upload_service import save_file_to_disk, create_file, get_file_by_id, list_files, update_file_status, delete_file

router = APIRouter(prefix="/file_upload", tags=["File Upload"])

# Pydantic schemas
class UploadedFileBase(BaseModel):
    session_id: UUID
    filename: str
    original_filename: str
    file_size: int
    status: str
    uploaded_at: datetime

class UploadedFileCreate(UploadedFileBase):
    pass

class UploadedFileUpdate(BaseModel):
    status: Optional[str] = None

class UploadedFileResponse(UploadedFileBase):
    id: UUID

# Routes
@router.post("/", response_model=UploadedFileResponse)
async def upload_file(
    session_id: UUID = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload an Excel file and save its metadata to the database.
    """
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are allowed.")

    # Save file to disk
    upload_dir = "uploads/"
    saved_path = save_file_to_disk(file, upload_dir)

    # Create file metadata in the database
    uploaded_file = create_file(
        session_id=session_id,
        filename=saved_path,
        original_filename=file.filename,
        file_size=file.spool_max_size,
        status="uploaded",
        db=db,
    )

    return UploadedFileResponse(**uploaded_file.__dict__)

@router.get("/", response_model=List[UploadedFileResponse])
async def list_uploaded_files(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    List all uploaded files for a given session.
    """
    files = list_files(session_id=session_id, db=db)
    return [UploadedFileResponse(**file.__dict__) for file in files]

@router.get("/{file_id}", response_model=UploadedFileResponse)
async def get_uploaded_file(
    file_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Retrieve metadata for a specific uploaded file.
    """
    file = get_file_by_id(file_id=file_id, db=db)
    if not file:
        raise HTTPException(status_code=404, detail="File not found.")
    return UploadedFileResponse(**file.__dict__)

@router.put("/{file_id}", response_model=UploadedFileResponse)
async def update_uploaded_file(
    file_id: UUID,
    file_update: UploadedFileUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Update the status of an uploaded file.
    """
    file = update_file_status(file_id=file_id, status=file_update.status, db=db)
    if not file:
        raise HTTPException(status_code=404, detail="File not found.")
    return UploadedFileResponse(**file.__dict__)

@router.delete("/{file_id}", response_model=dict)
async def delete_uploaded_file(
    file_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Delete an uploaded file and its metadata.
    """
    success = delete_file(file_id=file_id, db=db)
    if not success:
        raise HTTPException(status_code=404, detail="File not found.")
    return {"detail": "File deleted successfully."}