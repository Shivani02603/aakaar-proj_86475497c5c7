from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from ai.ingest import ingest
from ai.rag import answer

router = APIRouter(prefix="/api/ai")

# Request model for ingestion endpoint
class IngestRequest(BaseModel):
    file_path: str

# Response model for ingestion endpoint
class IngestResponse(BaseModel):
    success: bool
    message: str

# Request model for query endpoint
class QueryRequest(BaseModel):
    question: str

# Response model for query endpoint
class QueryResponse(BaseModel):
    answer: str
    citations: List[str]

@router.post("/ingest", response_model=IngestResponse)
async def ingest_endpoint(request: IngestRequest):
    """
    Endpoint to ingest an Excel file for processing.
    """
    try:
        success, message = ingest(request.file_path)
        return IngestResponse(success=success, message=message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    """
    Endpoint to handle user queries and return answers with citations.
    """
    try:
        answer_text, citations = answer(request.question)
        return QueryResponse(answer=answer_text, citations=citations)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))