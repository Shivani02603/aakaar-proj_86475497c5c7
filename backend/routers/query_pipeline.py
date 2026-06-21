from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from database.models import DocumentChunk, Message, UploadedFile, Session as DBSession
from database.config import get_db
from backend.services.auth import get_current_user
from ai.rag import embed_query, retrieve_context, answer_question
from datetime import datetime

router = APIRouter(prefix="/query_pipeline", tags=["Query Pipeline"])

# Pydantic models for request and response
class QueryRequest(BaseModel):
    query: str = Field(..., description="User's question")
    session_id: UUID = Field(..., description="Session ID associated with the query")
    top_k: int = Field(5, description="Number of top chunks to retrieve")

class QueryResponse(BaseModel):
    answer: str = Field(..., description="Generated answer from the AI model")
    citations: List[dict] = Field(..., description="Source citations for the answer")

class MessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    metadata: Optional[dict]
    created_at: datetime

# Endpoint to handle AI query
@router.post("/query", response_model=QueryResponse)
async def query_pipeline(
    request: QueryRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        # Validate session ownership
        session = db.query(DBSession).filter(DBSession.id == request.session_id).first()
        if not session or session.user_id != current_user["id"]:
            raise HTTPException(status_code=403, detail="Unauthorized access to session")

        # Embed the query
        query_embedding = embed_query(request.query)

        # Retrieve top chunks by cosine similarity
        top_chunks = retrieve_context(query_embedding, request.top_k, request.session_id, current_user["id"])
        if not top_chunks:
            raise HTTPException(status_code=404, detail="No relevant context found")

        # Build context for the AI model
        context = "\n".join([chunk["content"] for chunk in top_chunks])

        # Call the AI model to generate an answer
        answer_data = answer_question(request.query, context, current_user["id"])
        if not answer_data or "answer" not in answer_data or "citations" not in answer_data:
            raise HTTPException(status_code=500, detail="Failed to generate an answer")

        # Save user query and AI response to the database
        user_message = Message(
            id=UUID(),
            session_id=request.session_id,
            role="user",
            content=request.query,
            metadata=None,
            created_at=datetime.utcnow(),
        )
        assistant_message = Message(
            id=UUID(),
            session_id=request.session_id,
            role="assistant",
            content=answer_data["answer"],
            metadata={"citations": answer_data["citations"]},
            created_at=datetime.utcnow(),
        )
        db.add(user_message)
        db.add(assistant_message)
        db.commit()

        # Return the response
        return QueryResponse(answer=answer_data["answer"], citations=answer_data["citations"])
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

# Endpoint to list all messages in a session
@router.get("/{session_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        # Validate session ownership
        session = db.query(DBSession).filter(DBSession.id == session_id).first()
        if not session or session.user_id != current_user["id"]:
            raise HTTPException(status_code=403, detail="Unauthorized access to session")

        # Retrieve messages
        messages = db.query(Message).filter(Message.session_id == session_id).order_by(Message.created_at.asc()).all()
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
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred")