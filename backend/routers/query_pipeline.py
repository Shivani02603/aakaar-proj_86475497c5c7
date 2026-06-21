from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from database.models import DocumentChunk, UploadedFile, Message
from database.config import get_db
from backend.services.auth import get_current_user
from backend.routers.query_pipeline import embed_query, retrieve_top_chunks, build_prompt_context, call_llm

router = APIRouter(prefix="/query_pipeline", tags=["Query Pipeline"])

class QueryRequest(BaseModel):
    query: str = Field(..., description="The user's question or query.")
    session_id: UUID = Field(..., description="The session ID associated with the query.")
    top_k: int = Field(5, description="Number of top chunks to retrieve based on similarity.")

class QueryResponse(BaseModel):
    answer: str = Field(..., description="The generated answer to the user's query.")
    citations: List[Dict[str, Any]] = Field(..., description="List of source citations for the answer.")

@router.post("/query", response_model=QueryResponse)
async def query_pipeline(request: QueryRequest, db: Session = Depends(get_db), current_user: Any = Depends(get_current_user)):
    """
    Handles user queries by embedding the query, retrieving relevant chunks, and generating an answer using an LLM.
    """
    # Step 1: Embed the query
    try:
        query_embedding = embed_query(request.query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to embed query: {str(e)}")

    # Step 2: Retrieve top chunks based on cosine similarity
    try:
        top_chunks = retrieve_top_chunks(query_embedding, request.top_k, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve top chunks: {str(e)}")

    # Step 3: Build context for the LLM
    try:
        context = build_prompt_context(top_chunks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to build prompt context: {str(e)}")

    # Step 4: Call the LLM to generate an answer
    try:
        messages = [{"role": "user", "content": request.query}, {"role": "system", "content": context}]
        answer = call_llm(messages, stream=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate answer: {str(e)}")

    # Step 5: Prepare citations
    citations = []
    for chunk in top_chunks:
        citations.append({
            "filename": chunk.metadata.get("filename"),
            "row_range": chunk.metadata.get("row_range"),
        })

    # Step 6: Return the response
    return QueryResponse(answer=answer, citations=citations)

@router.get("/chunks", response_model=List[DocumentChunk])
async def list_chunks(file_id: UUID, db: Session = Depends(get_db), current_user: Any = Depends(get_current_user)):
    """
    Lists all chunks associated with a specific file.
    """
    try:
        chunks = db.query(DocumentChunk).filter(DocumentChunk.file_id == file_id).all()
        return chunks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list chunks: {str(e)}")

@router.get("/chunks/{chunk_id}", response_model=DocumentChunk)
async def get_chunk(chunk_id: UUID, db: Session = Depends(get_db), current_user: Any = Depends(get_current_user)):
    """
    Retrieves a specific chunk by its ID.
    """
    try:
        chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
        if not chunk:
            raise HTTPException(status_code=404, detail="Chunk not found.")
        return chunk
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve chunk: {str(e)}")

@router.post("/chunks", response_model=DocumentChunk)
async def create_chunk(chunk: DocumentChunk, db: Session = Depends(get_db), current_user: Any = Depends(get_current_user)):
    """
    Creates a new chunk in the database.
    """
    try:
        db.add(chunk)
        db.commit()
        db.refresh(chunk)
        return chunk
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create chunk: {str(e)}")

@router.put("/chunks/{chunk_id}", response_model=DocumentChunk)
async def update_chunk(chunk_id: UUID, chunk_update: DocumentChunk, db: Session = Depends(get_db), current_user: Any = Depends(get_current_user)):
    """
    Updates an existing chunk in the database.
    """
    try:
        chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
        if not chunk:
            raise HTTPException(status_code=404, detail="Chunk not found.")
        for key, value in chunk_update.dict().items():
            setattr(chunk, key, value)
        db.commit()
        db.refresh(chunk)
        return chunk
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update chunk: {str(e)}")

@router.delete("/chunks/{chunk_id}")
async def delete_chunk(chunk_id: UUID, db: Session = Depends(get_db), current_user: Any = Depends(get_current_user)):
    """
    Deletes a chunk from the database.
    """
    try:
        chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
        if not chunk:
            raise HTTPException(status_code=404, detail="Chunk not found.")
        db.delete(chunk)
        db.commit()
        return {"detail": "Chunk deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete chunk: {str(e)}")