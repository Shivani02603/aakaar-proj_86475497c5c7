from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from database.models import User, Session as DBSession, UploadedFile, Message
from database.config import get_db
from backend.services.auth import get_current_user
from datetime import datetime

router = APIRouter(prefix="/frontend", tags=["Frontend"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Pydantic Schemas
class SessionCreateRequest(BaseModel):
    name: str = Field(..., example="New Session")

class SessionResponse(BaseModel):
    id: UUID
    name: str
    created_at: datetime

class FileUploadRequest(BaseModel):
    filename: str
    original_filename: str
    file_size: int

class FileResponse(BaseModel):
    id: UUID
    filename: str
    original_filename: str
    file_size: int
    status: str
    uploaded_at: datetime

class MessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    metadata: Optional[dict]
    created_at: datetime

# Routes
@router.post("/sessions", response_model=SessionResponse)
def create_session(
    session_data: SessionCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_session = DBSession(
        user_id=current_user.id,
        name=session_data.name,
        created_at=datetime.utcnow(),
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return SessionResponse(
        id=new_session.id,
        name=new_session.name,
        created_at=new_session.created_at,
    )

@router.get("/sessions", response_model=List[SessionResponse])
def list_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sessions = db.query(DBSession).filter(DBSession.user_id == current_user.id).all()
    return [
        SessionResponse(
            id=session.id,
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
    session = db.query(DBSession).filter(DBSession.id == session_id, DBSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionResponse(
        id=session.id,
        name=session.name,
        created_at=session.created_at,
    )

@router.post("/sessions/{session_id}/files", response_model=FileResponse)
def upload_file(
    session_id: UUID,
    file_data: FileUploadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = db.query(DBSession).filter(DBSession.id == session_id, DBSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    new_file = UploadedFile(
        session_id=session_id,
        filename=file_data.filename,
        original_filename=file_data.original_filename,
        file_size=file_data.file_size,
        status="uploaded",
        uploaded_at=datetime.utcnow(),
    )
    db.add(new_file)
    db.commit()
    db.refresh(new_file)
    return FileResponse(
        id=new_file.id,
        filename=new_file.filename,
        original_filename=new_file.original_filename,
        file_size=new_file.file_size,
        status=new_file.status,
        uploaded_at=new_file.uploaded_at,
    )

@router.get("/sessions/{session_id}/files", response_model=List[FileResponse])
def list_files(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = db.query(DBSession).filter(DBSession.id == session_id, DBSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    files = db.query(UploadedFile).filter(UploadedFile.session_id == session_id).all()
    return [
        FileResponse(
            id=file.id,
            filename=file.filename,
            original_filename=file.original_filename,
            file_size=file.file_size,
            status=file.status,
            uploaded_at=file.uploaded_at,
        )
        for file in files
    ]

@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
def get_messages(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = db.query(DBSession).filter(DBSession.id == session_id, DBSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = db.query(Message).filter(Message.session_id == session_id).order_by(Message.created_at.desc()).all()
    return [
        MessageResponse(
            id=message.id,
            role=message.role,
            content=message.content,
            metadata=message.metadata,
            created_at=message.created_at,
        )
        for message in messages
    ]

@router.delete("/sessions/{session_id}", status_code=204)
def delete_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = db.query(DBSession).filter(DBSession.id == session_id, DBSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(session)
    db.commit()
    return

@router.delete("/sessions/{session_id}/files/{file_id}", status_code=204)
def delete_file(
    session_id: UUID,
    file_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = db.query(DBSession).filter(DBSession.id == session_id, DBSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    file = db.query(UploadedFile).filter(UploadedFile.id == file_id, UploadedFile.session_id == session_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    db.delete(file)
    db.commit()
    return

@router.delete("/sessions/{session_id}/messages/{message_id}", status_code=204)
def delete_message(
    session_id: UUID,
    message_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = db.query(DBSession).filter(DBSession.id == session_id, DBSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    message = db.query(Message).filter(Message.id == message_id, Message.session_id == session_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    db.delete(message)
    db.commit()
    return