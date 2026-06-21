from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from database.models import DocumentChunk, UploadedFile
from database.config import get_db
from backend.services.auth import get_current_user
from ai.embeddings import embed_batch
from ai.ingest import chunk
from datetime import datetime
import os
import pandas as pd

router = APIRouter(prefix="/ingestion_pipeline", tags=["Ingestion Pipeline"])

# Pydantic schemas
class DocumentChunkBase(BaseModel):
    file_id: UUID
    content: str
    metadata: Optional[dict] = None
    chunk_index: int

class DocumentChunkCreate(DocumentChunkBase):
    pass

class DocumentChunkResponse(DocumentChunkBase):
    id: UUID
    created_at: datetime

class IngestRequest(BaseModel):
    session_id: UUID
    file: UploadFile

class IngestResponse(BaseModel):
    message: str
    chunks_created: int

# Helper functions
def parse_excel(file_path: str) -> List[str]:
    try:
        df = pd.read_excel(file_path)
        content = df.to_string(index=False)
        return [content]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing Excel file: {str(e)}")

def store_chunks(chunks: List[DocumentChunkCreate], db: Session):
    try:
        for chunk_data in chunks:
            chunk = DocumentChunk(**chunk_data.dict())
            db.add(chunk)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error storing chunks: {str(e)}")

# Routes
@router.post("/ingest", response_model=IngestResponse)
async def ingest_documents(
    session_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    # Validate session ownership
    session = db.query(UploadedFile).filter(UploadedFile.session_id == session_id).first()
    if not session or session.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Unauthorized access to session.")

    # Save file to disk
    upload_dir = os.getenv("UPLOAD_DIRECTORY", "/tmp/uploads")
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as f:
        f.write(file.file.read())

    # Parse Excel file
    try:
        parsed_content = parse_excel(file_path)
    except HTTPException as e:
        raise e

    # Chunk content
    try:
        chunks = chunk(parsed_content, chunk_size=1000, overlap=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error chunking content: {str(e)}")

    # Embed chunks
    try:
        embeddings = embed_batch([chunk.content for chunk in chunks])
        for i, embedding in enumerate(embeddings):
            chunks[i].embedding = embedding
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error embedding chunks: {str(e)}")

    # Store chunks in database
    try:
        store_chunks(chunks, db)
    except HTTPException as e:
        raise e

    return IngestResponse(message="Document ingestion successful.", chunks_created=len(chunks))

@router.get("/chunks", response_model=List[DocumentChunkResponse])
def list_chunks(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    chunks = db.query(DocumentChunk).all()
    return [DocumentChunkResponse(**chunk.__dict__) for chunk in chunks]

@router.get("/chunks/{chunk_id}", response_model=DocumentChunkResponse)
def get_chunk(chunk_id: UUID, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(status_code=404, detail="Chunk not found.")
    return DocumentChunkResponse(**chunk.__dict__)

@router.put("/chunks/{chunk_id}", response_model=DocumentChunkResponse)
def update_chunk(
    chunk_id: UUID,
    chunk_update: DocumentChunkCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(status_code=404, detail="Chunk not found.")
    for key, value in chunk_update.dict().items():
        setattr(chunk, key, value)
    db.commit()
    return DocumentChunkResponse(**chunk.__dict__)

@router.delete("/chunks/{chunk_id}", status_code=204)
def delete_chunk(chunk_id: UUID, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(status_code=404, detail="Chunk not found.")
    db.delete(chunk)
    db.commit()