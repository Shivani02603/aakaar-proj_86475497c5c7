from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from database.models import DocumentChunk, UploadedFile
from database.config import get_db
from backend.services.auth import jwt_auth_dependency
from backend.routers.ingestion_pipeline import chunk_text
from ai.embeddings import embed_batch
from ai.vector_store import upsert
import pandas as pd
import os
import tempfile

router = APIRouter(prefix="/ingestion_pipeline", tags=["Ingestion Pipeline"])

# Pydantic schemas
class ChunkRequest(BaseModel):
    file_id: UUID
    content: str
    chunk_index: int
    metadata: Optional[dict] = None

class ChunkResponse(BaseModel):
    id: UUID
    file_id: UUID
    content: str
    embedding: List[float]
    metadata: Optional[dict]
    chunk_index: int
    created_at: datetime

class FileUploadRequest(BaseModel):
    session_id: UUID
    filename: str
    original_filename: str
    file_size: int
    status: str

class FileUploadResponse(BaseModel):
    id: UUID
    session_id: UUID
    filename: str
    original_filename: str
    file_size: int
    status: str
    uploaded_at: datetime

# Helper functions
def parse_excel(file_path: str) -> List[str]:
    try:
        df = pd.read_excel(file_path)
        return df.to_string(index=False).splitlines()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing Excel file: {str(e)}")

def store_chunks(chunks: List[dict], db: Session):
    for chunk in chunks:
        db_chunk = DocumentChunk(**chunk)
        db.add(db_chunk)
    db.commit()

# Routes
@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    session_id: UUID = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(jwt_auth_dependency),
):
    try:
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(file.file.read())
            tmp_file_path = tmp_file.name

        # Parse Excel file
        parsed_content = parse_excel(tmp_file_path)

        # Chunk content
        chunks = chunk_text(parsed_content, chunk_size=1000, overlap=200)

        # Embed chunks
        embeddings = embed_batch([chunk["content"] for chunk in chunks])

        # Store chunks in DB
        for i, chunk in enumerate(chunks):
            chunk["embedding"] = embeddings[i]
            chunk["file_id"] = session_id
            chunk["created_at"] = datetime.utcnow()
        store_chunks(chunks, db)

        # Store file metadata in DB
        uploaded_file = UploadedFile(
            session_id=session_id,
            filename=file.filename,
            original_filename=file.filename,
            file_size=len(file.file.read()),
            status="processed",
            uploaded_at=datetime.utcnow(),
        )
        db.add(uploaded_file)
        db.commit()

        return FileUploadResponse(
            id=uploaded_file.id,
            session_id=uploaded_file.session_id,
            filename=uploaded_file.filename,
            original_filename=uploaded_file.original_filename,
            file_size=uploaded_file.file_size,
            status=uploaded_file.status,
            uploaded_at=uploaded_file.uploaded_at,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)

@router.get("/chunks/{file_id}", response_model=List[ChunkResponse])
async def list_chunks(file_id: UUID, db: Session = Depends(get_db)):
    chunks = db.query(DocumentChunk).filter(DocumentChunk.file_id == file_id).all()
    return [
        ChunkResponse(
            id=chunk.id,
            file_id=chunk.file_id,
            content=chunk.content,
            embedding=chunk.embedding,
            metadata=chunk.metadata,
            chunk_index=chunk.chunk_index,
            created_at=chunk.created_at,
        )
        for chunk in chunks
    ]

@router.get("/chunks/{chunk_id}", response_model=ChunkResponse)
async def get_chunk(chunk_id: UUID, db: Session = Depends(get_db)):
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(status_code=404, detail="Chunk not found")
    return ChunkResponse(
        id=chunk.id,
        file_id=chunk.file_id,
        content=chunk.content,
        embedding=chunk.embedding,
        metadata=chunk.metadata,
        chunk_index=chunk.chunk_index,
        created_at=chunk.created_at,
    )

@router.delete("/chunks/{chunk_id}")
async def delete_chunk(chunk_id: UUID, db: Session = Depends(get_db)):
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(status_code=404, detail="Chunk not found")
    db.delete(chunk)
    db.commit()
    return {"detail": "Chunk deleted successfully"}