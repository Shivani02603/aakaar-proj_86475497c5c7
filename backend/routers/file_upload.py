from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from database.models import UploadedFile, Session as DBSession
from database.config import get_db
from backend.services.auth import get_current_user
from backend.services.file_upload_service import save_uploaded_file, delete_file, get_file_by_id, list_files
from ai.ingest import ingest_excel

router = APIRouter(prefix="/file_upload", tags=["File Upload"])

# Pydantic Schemas
class UploadedFileBase(BaseModel):
    session_id: UUID
    filename: str
    original_filename: str
    file_size: int
    status: str

class UploadedFileCreate(UploadedFileBase):
    pass

class UploadedFileResponse(UploadedFileBase):
    id: UUID
    uploaded_at: str

class UploadedFileUpdate(BaseModel):
    status: Optional[str]

# Endpoint: Upload File
@router.post("/", response_model=UploadedFileResponse)
async def upload_file(
    session_id: UUID = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    # Validate session ownership
    db_session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if not db_session or db_session.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Unauthorized access to session.")

    # Save file to disk
    try:
        file_path = save_uploaded_file(file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Process Excel file
    try:
        ingest_excel(file_path, session_id, current_user["id"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")

    # Create UploadedFile record
    uploaded_file = UploadedFile(
        session_id=session_id,
        filename=file.filename,
        original_filename=file.filename,
        file_size=len(file.file.read()),
        status="uploaded",
    )
    db.add(uploaded_file)
    db.commit()
    db.refresh(uploaded_file)

    return UploadedFileResponse(
        id=uploaded_file.id,
        session_id=uploaded_file.session_id,
        filename=uploaded_file.filename,
        original_filename=uploaded_file.original_filename,
        file_size=uploaded_file.file_size,
        status=uploaded_file.status,
        uploaded_at=uploaded_file.uploaded_at.isoformat(),
    )

# Endpoint: List Files
@router.get("/", response_model=List[UploadedFileResponse])
async def list_uploaded_files(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    # Validate session ownership
    db_session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if not db_session or db_session.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Unauthorized access to session.")

    files = list_files(session_id, db)
    return [
        UploadedFileResponse(
            id=file.id,
            session_id=file.session_id,
            filename=file.filename,
            original_filename=file.original_filename,
            file_size=file.file_size,
            status=file.status,
            uploaded_at=file.uploaded_at.isoformat(),
        )
        for file in files
    ]

# Endpoint: Get File by ID
@router.get("/{file_id}", response_model=UploadedFileResponse)
async def get_uploaded_file(
    file_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    file = get_file_by_id(file_id, db)
    if not file or file.session.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Unauthorized access to file.")

    return UploadedFileResponse(
        id=file.id,
        session_id=file.session_id,
        filename=file.filename,
        original_filename=file.original_filename,
        file_size=file.file_size,
        status=file.status,
        uploaded_at=file.uploaded_at.isoformat(),
    )

# Endpoint: Update File
@router.put("/{file_id}", response_model=UploadedFileResponse)
async def update_uploaded_file(
    file_id: UUID,
    file_update: UploadedFileUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    file = get_file_by_id(file_id, db)
    if not file or file.session.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Unauthorized access to file.")

    if file_update.status:
        file.status = file_update.status

    db.commit()
    db.refresh(file)

    return UploadedFileResponse(
        id=file.id,
        session_id=file.session_id,
        filename=file.filename,
        original_filename=file.original_filename,
        file_size=file.file_size,
        status=file.status,
        uploaded_at=file.uploaded_at.isoformat(),
    )

# Endpoint: Delete File
@router.delete("/{file_id}", status_code=204)
async def delete_uploaded_file(
    file_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    file = get_file_by_id(file_id, db)
    if not file or file.session.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Unauthorized access to file.")

    delete_file(file_id, db)