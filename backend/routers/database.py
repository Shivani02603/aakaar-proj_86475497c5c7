from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from database.models import User, Session as DBSession, UploadedFile, DocumentChunk, Message
from database.config import get_db
from backend.services.auth import jwt_auth_dependency

router = APIRouter(prefix="/database", tags=["Database"])

# Pydantic Schemas
class UserSchema(BaseModel):
    id: UUID
    email: str
    created_at: datetime

    class Config:
        orm_mode = True


class UserCreate(BaseModel):
    email: str


class UserUpdate(BaseModel):
    email: Optional[str]


class SessionSchema(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    created_at: datetime

    class Config:
        orm_mode = True


class SessionCreate(BaseModel):
    user_id: UUID
    name: str


class SessionUpdate(BaseModel):
    name: Optional[str]


class UploadedFileSchema(BaseModel):
    id: UUID
    session_id: UUID
    filename: str
    original_filename: str
    file_size: int
    status: str
    uploaded_at: datetime

    class Config:
        orm_mode = True


class UploadedFileCreate(BaseModel):
    session_id: UUID
    filename: str
    original_filename: str
    file_size: int
    status: str


class UploadedFileUpdate(BaseModel):
    status: Optional[str]


class DocumentChunkSchema(BaseModel):
    id: UUID
    file_id: UUID
    content: str
    embedding: List[float]
    metadata: dict
    chunk_index: int
    created_at: datetime

    class Config:
        orm_mode = True


class DocumentChunkCreate(BaseModel):
    file_id: UUID
    content: str
    embedding: List[float]
    metadata: dict
    chunk_index: int


class DocumentChunkUpdate(BaseModel):
    metadata: Optional[dict]


class MessageSchema(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    metadata: dict
    created_at: datetime

    class Config:
        orm_mode = True


class MessageCreate(BaseModel):
    session_id: UUID
    role: str
    content: str
    metadata: dict


class MessageUpdate(BaseModel):
    content: Optional[str]
    metadata: Optional[dict]


# CRUD Endpoints for User
@router.get("/users", response_model=List[UserSchema])
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users


@router.get("/users/{user_id}", response_model=UserSchema)
def get_user(user_id: UUID, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.post("/users", response_model=UserSchema)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    new_user = User(email=user.email, created_at=datetime.utcnow())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.put("/users/{user_id}", response_model=UserSchema)
def update_user(user_id: UUID, user_update: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user_update.email:
        user.email = user_update.email
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: UUID, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    db.delete(user)
    db.commit()
    return None


# CRUD Endpoints for Session
@router.get("/sessions", response_model=List[SessionSchema])
def list_sessions(db: Session = Depends(get_db)):
    sessions = db.query(DBSession).all()
    return sessions


@router.get("/sessions/{session_id}", response_model=SessionSchema)
def get_session(session_id: UUID, db: Session = Depends(get_db)):
    session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session


@router.post("/sessions", response_model=SessionSchema)
def create_session(session: SessionCreate, db: Session = Depends(get_db)):
    new_session = DBSession(user_id=session.user_id, name=session.name, created_at=datetime.utcnow())
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session


@router.put("/sessions/{session_id}", response_model=SessionSchema)
def update_session(session_id: UUID, session_update: SessionUpdate, db: Session = Depends(get_db)):
    session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session_update.name:
        session.name = session_update.name
    db.commit()
    db.refresh(session)
    return session


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: UUID, db: Session = Depends(get_db)):
    session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    db.delete(session)
    db.commit()
    return None


# CRUD Endpoints for UploadedFile
@router.get("/files", response_model=List[UploadedFileSchema])
def list_files(db: Session = Depends(get_db)):
    files = db.query(UploadedFile).all()
    return files


@router.get("/files/{file_id}", response_model=UploadedFileSchema)
def get_file(file_id: UUID, db: Session = Depends(get_db)):
    file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return file


@router.post("/files", response_model=UploadedFileSchema)
def create_file(file: UploadedFileCreate, db: Session = Depends(get_db)):
    new_file = UploadedFile(
        session_id=file.session_id,
        filename=file.filename,
        original_filename=file.original_filename,
        file_size=file.file_size,
        status=file.status,
        uploaded_at=datetime.utcnow(),
    )
    db.add(new_file)
    db.commit()
    db.refresh(new_file)
    return new_file


@router.put("/files/{file_id}", response_model=UploadedFileSchema)
def update_file(file_id: UUID, file_update: UploadedFileUpdate, db: Session = Depends(get_db)):
    file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    if file_update.status:
        file.status = file_update.status
    db.commit()
    db.refresh(file)
    return file


@router.delete("/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(file_id: UUID, db: Session = Depends(get_db)):
    file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    db.delete(file)
    db.commit()
    return None


# CRUD Endpoints for DocumentChunk
@router.get("/chunks", response_model=List[DocumentChunkSchema])
def list_chunks(db: Session = Depends(get_db)):
    chunks = db.query(DocumentChunk).all()
    return chunks


@router.get("/chunks/{chunk_id}", response_model=DocumentChunkSchema)
def get_chunk(chunk_id: UUID, db: Session = Depends(get_db)):
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chunk not found")
    return chunk


@router.post("/chunks", response_model=DocumentChunkSchema)
def create_chunk(chunk: DocumentChunkCreate, db: Session = Depends(get_db)):
    new_chunk = DocumentChunk(
        file_id=chunk.file_id,
        content=chunk.content,
        embedding=chunk.embedding,
        metadata=chunk.metadata,
        chunk_index=chunk.chunk_index,
        created_at=datetime.utcnow(),
    )
    db.add(new_chunk)
    db.commit()
    db.refresh(new_chunk)
    return new_chunk


@router.put("/chunks/{chunk_id}", response_model=DocumentChunkSchema)
def update_chunk(chunk_id: UUID, chunk_update: DocumentChunkUpdate, db: Session = Depends(get_db)):
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chunk not found")
    if chunk_update.metadata:
        chunk.metadata = chunk_update.metadata
    db.commit()
    db.refresh(chunk)
    return chunk


@router.delete("/chunks/{chunk_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chunk(chunk_id: UUID, db: Session = Depends(get_db)):
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chunk not found")
    db.delete(chunk)
    db.commit()
    return None


# CRUD Endpoints for Message
@router.get("/messages", response_model=List[MessageSchema])
def list_messages(db: Session = Depends(get_db)):
    messages = db.query(Message).all()
    return messages


@router.get("/messages/{message_id}", response_model=MessageSchema)
def get_message(message_id: UUID, db: Session = Depends(get_db)):
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    return message


@router.post("/messages", response_model=MessageSchema)
def create_message(message: MessageCreate, db: Session = Depends(get_db)):
    new_message = Message(
        session_id=message.session_id,
        role=message.role,
        content=message.content,
        metadata=message.metadata,
        created_at=datetime.utcnow(),
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return new_message


@router.put("/messages/{message_id}", response_model=MessageSchema)
def update_message(message_id: UUID, message_update: MessageUpdate, db: Session = Depends(get_db)):
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    if message_update.content:
        message.content = message_update.content
    if message_update.metadata:
        message.metadata = message_update.metadata
    db.commit()
    db.refresh(message)
    return message


@router.delete("/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(message_id: UUID, db: Session = Depends(get_db)):
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    db.delete(message)
    db.commit()
    return None