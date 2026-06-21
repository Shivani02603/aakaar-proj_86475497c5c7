from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from database.models import User, Session as DBSession, UploadedFile, DocumentChunk, Message
from database.config import get_db
from backend.services.auth import get_current_user

router = APIRouter(prefix="/backend", tags=["Backend"])

# Pydantic Schemas
class UserBase(BaseModel):
    email: str = Field(..., example="user@example.com")

class UserCreate(UserBase):
    password: str = Field(..., example="strongpassword123")

class UserResponse(UserBase):
    id: UUID
    created_at: str

class UserUpdate(BaseModel):
    email: Optional[str] = Field(None, example="newemail@example.com")
    password: Optional[str] = Field(None, example="newpassword123")

class SessionBase(BaseModel):
    name: str = Field(..., example="My Session")

class SessionCreate(SessionBase):
    pass

class SessionResponse(SessionBase):
    id: UUID
    user_id: UUID
    created_at: str

class SessionUpdate(BaseModel):
    name: Optional[str] = Field(None, example="Updated Session Name")

class UploadedFileBase(BaseModel):
    filename: str = Field(..., example="document.pdf")
    original_filename: str = Field(..., example="original_document.pdf")
    file_size: int = Field(..., example=1024)

class UploadedFileCreate(UploadedFileBase):
    pass

class UploadedFileResponse(UploadedFileBase):
    id: UUID
    session_id: UUID
    status: str
    uploaded_at: str

class UploadedFileUpdate(BaseModel):
    filename: Optional[str] = Field(None, example="updated_document.pdf")
    original_filename: Optional[str] = Field(None, example="updated_original_document.pdf")
    file_size: Optional[int] = Field(None, example=2048)

class DocumentChunkBase(BaseModel):
    content: str = Field(..., example="Chunk content")
    metadata: dict = Field(..., example={"source": "document.pdf"})
    chunk_index: int = Field(..., example=0)

class DocumentChunkCreate(DocumentChunkBase):
    pass

class DocumentChunkResponse(DocumentChunkBase):
    id: UUID
    file_id: UUID
    embedding: List[float]
    created_at: str

class DocumentChunkUpdate(BaseModel):
    content: Optional[str] = Field(None, example="Updated chunk content")
    metadata: Optional[dict] = Field(None, example={"source": "updated_document.pdf"})
    chunk_index: Optional[int] = Field(None, example=1)

class MessageBase(BaseModel):
    role: str = Field(..., example="user")
    content: str = Field(..., example="Hello, how are you?")
    metadata: dict = Field(..., example={"source": "chat"})

class MessageCreate(MessageBase):
    pass

class MessageResponse(MessageBase):
    id: UUID
    session_id: UUID
    created_at: str

class MessageUpdate(BaseModel):
    role: Optional[str] = Field(None, example="assistant")
    content: Optional[str] = Field(None, example="I'm fine, thank you!")
    metadata: Optional[dict] = Field(None, example={"source": "updated_chat"})

# CRUD Endpoints for User
@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(email=user.email, password=user.password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/users", response_model=List[UserResponse])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).all()

@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: UUID, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: UUID, user_update: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user_update.email:
        user.email = user_update.email
    if user_update.password:
        user.password = user_update.password
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
    return

# CRUD Endpoints for Session
@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(session: SessionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_session = DBSession(name=session.name, user_id=current_user.id)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

@router.get("/sessions", response_model=List[SessionResponse])
def list_sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(DBSession).filter(DBSession.user_id == current_user.id).all()

@router.get("/sessions/{session_id}", response_model=SessionResponse)
def get_session(session_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(DBSession).filter(DBSession.id == session_id, DBSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session

@router.put("/sessions/{session_id}", response_model=SessionResponse)
def update_session(session_id: UUID, session_update: SessionUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(DBSession).filter(DBSession.id == session_id, DBSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session_update.name:
        session.name = session_update.name
    db.commit()
    db.refresh(session)
    return session

@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(DBSession).filter(DBSession.id == session_id, DBSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    db.delete(session)
    db.commit()
    return

# CRUD Endpoints for UploadedFile
@router.post("/files", response_model=UploadedFileResponse, status_code=status.HTTP_201_CREATED)
def create_file(file: UploadedFileCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_file = UploadedFile(**file.dict(), user_id=current_user.id)
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file

@router.get("/files", response_model=List[UploadedFileResponse])
def list_files(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(UploadedFile).filter(UploadedFile.user_id == current_user.id).all()

@router.get("/files/{file_id}", response_model=UploadedFileResponse)
def get_file(file_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    file = db.query(UploadedFile).filter(UploadedFile.id == file_id, UploadedFile.user_id == current_user.id).first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return file

@router.put("/files/{file_id}", response_model=UploadedFileResponse)
def update_file(file_id: UUID, file_update: UploadedFileUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    file = db.query(UploadedFile).filter(UploadedFile.id == file_id, UploadedFile.user_id == current_user.id).first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    for key, value in file_update.dict(exclude_unset=True).items():
        setattr(file, key, value)
    db.commit()
    db.refresh(file)
    return file

@router.delete("/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(file_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    file = db.query(UploadedFile).filter(UploadedFile.id == file_id, UploadedFile.user_id == current_user.id).first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    db.delete(file)
    db.commit()
    return