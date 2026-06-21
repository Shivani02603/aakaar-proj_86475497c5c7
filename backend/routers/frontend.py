from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from database.models import User, Session, UploadedFile, Message, DocumentChunk
from database.config import get_db
from backend.services.auth import get_current_user
from backend.services.file_upload_service import save_file_to_disk, upload_file
from backend.services.backend_service import BackendService
from backend.services.frontend_service import FrontendService

router = APIRouter(prefix="/frontend", tags=["Frontend"])

# Pydantic Schemas
class SessionCreateRequest(BaseModel):
    name: str = Field(..., example="New Session")

class SessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    created_at: datetime

class FileUploadRequest(BaseModel):
    session_id: UUID
    filename: str
    original_filename: str
    file_size: int

class FileResponse(BaseModel):
    id: UUID
    session_id: UUID
    filename: str
    original_filename: str
    file_size: int
    status: str
    uploaded_at: datetime

class MessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    metadata: Optional[Dict[str, Any]]
    created_at: datetime

# Endpoints
@router.post("/sessions", response_model=SessionResponse)
def create_session(
    session_data: SessionCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    backend_service = BackendService(db)
    session = backend_service.create_session(
        user_id=current_user.id, name=session_data.name
    )
    return SessionResponse(
        id=session.id,
        user_id=session.user_id,
        name=session.name,
        created_at=session.created_at,
    )

@router.get("/sessions", response_model=List[SessionResponse])
def list_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    backend_service = BackendService(db)
    sessions = backend_service.list_sessions(user_id=current_user.id)
    return [
        SessionResponse(
            id=session.id,
            user_id=session.user_id,
            name=session.name,
            created_at=session.created_at,
        )
        for session in sessions
    ]

@router.get("/sessions/{session_id}", response_model=SessionResponse)
def get_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    backend_service = BackendService(db)
    session = backend_service.get_session_by_id(session_id=session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionResponse(
        id=session.id,
        user_id=session.user_id,
        name=session.name,
        created_at=session.created_at,
    )

@router.post("/sessions/{session_id}/files", response_model=FileResponse)
def upload_file_to_session(
    session_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    backend_service = BackendService(db)
    session = backend_service.get_session_by_id(session_id=session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    upload_dir = "/uploads"
    saved_path = save_file_to_disk(file, upload_dir)
    file_upload_service = FrontendService(db)
    uploaded_file = file_upload_service.create_file(
        session_id=session_id,
        filename=saved_path,
        original_filename=file.filename,
        file_size=file.spool_max_size,
    )
    return FileResponse(
        id=uploaded_file.id,
        session_id=uploaded_file.session_id,
        filename=uploaded_file.filename,
        original_filename=uploaded_file.original_filename,
        file_size=uploaded_file.file_size,
        status=uploaded_file.status,
        uploaded_at=uploaded_file.uploaded_at,
    )

@router.get("/sessions/{session_id}/files", response_model=List[FileResponse])
def list_files_in_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    backend_service = BackendService(db)
    session = backend_service.get_session_by_id(session_id=session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    file_upload_service = FrontendService(db)
    files = file_upload_service.list_files_by_session(session_id=session_id)
    return [
        FileResponse(
            id=file.id,
            session_id=file.session_id,
            filename=file.filename,
            original_filename=file.original_filename,
            file_size=file.file_size,
            status=file.status,
            uploaded_at=file.uploaded_at,
        )
        for file in files
    ]

@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
def get_messages_in_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    backend_service = BackendService(db)
    session = backend_service.get_session_by_id(session_id=session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    frontend_service = FrontendService(db)
    messages = frontend_service.get_messages_by_session(session_id=session_id)
    return [
        MessageResponse(
            id=message.id,
            session_id=message.session_id,
            role=message.role,
            content=message.content,
            metadata=message.metadata,
            created_at=message.created_at,
        )
        for message in messages
    ]