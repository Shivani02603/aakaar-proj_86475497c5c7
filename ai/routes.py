from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List
from ai.ingest import ingest
from ai.rag import answer

router = APIRouter(prefix="/api/ai")

class IngestRequest(BaseModel):
    file: UploadFile

class IngestResponse(BaseModel):
    message: str
    file_name: str

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str
    citations: List[str]

@router.post("/ingest", response_model=IngestResponse)
async def ingest_file(file: UploadFile = File(...)):
    """
    Endpoint to handle file ingestion.
    """
    try:
        file_name = await ingest(file)
        return IngestResponse(message="File ingested successfully", file_name=file_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query", response_model=QueryResponse)
async def query_ai(request: QueryRequest):
    """
    Endpoint to handle user queries.
    """
    try:
        answer_text, citations = await answer(request.question)
        return QueryResponse(answer=answer_text, citations=citations)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))