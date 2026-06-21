import os
from uuid import UUID
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from database.models import DocumentChunk, UploadedFile
from env import OPENAI_API_KEY
from ai.embeddings import embed_batch
from ai.ingest import parse_excel
from pydantic import BaseModel
from langchain.text_splitter import RecursiveCharacterTextSplitter

if not OPENAI_API_KEY:
    raise HTTPException(status_code=500, detail="OpenAI API key not configured")

class IngestionPipelineService:
    @staticmethod
    async def parse_excel(file_path: str) -> List[str]:
        try:
            return parse_excel(file_path)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error parsing Excel file: {str(e)}")

    @staticmethod
    def split_content_into_chunks(content: str) -> List[str]:
        try:
            splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            return splitter.split_text(content)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error splitting content into chunks: {str(e)}")

    @staticmethod
    async def embed_chunks(chunks: List[str]) -> List[List[float]]:
        try:
            return embed_batch(chunks)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error embedding chunks: {str(e)}")

    @staticmethod
    async def store_chunks(chunks: List[str], embeddings: List[List[float]], file_id: UUID, db: AsyncSession):
        try:
            for index, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                document_chunk = DocumentChunk(
                    file_id=file_id,
                    content=chunk,
                    embedding=embedding,
                    metadata={},
                    chunk_index=index,
                )
                db.add(document_chunk)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Error storing chunks in database: {str(e)}")

    @staticmethod
    async def create_chunks_from_excel(file_path: str, file_id: UUID, db: AsyncSession):
        try:
            # Parse the Excel file
            parsed_content = IngestionPipelineService.parse_excel(file_path)

            # Split content into chunks
            all_chunks = []
            for content in parsed_content:
                chunks = IngestionPipelineService.split_content_into_chunks(content)
                all_chunks.extend(chunks)

            # Embed chunks
            embeddings = await IngestionPipelineService.embed_chunks(all_chunks)

            # Store chunks in the database
            await IngestionPipelineService.store_chunks(all_chunks, embeddings, file_id, db)
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing Excel file: {str(e)}")

    @staticmethod
    async def get_chunk_by_id(chunk_id: UUID, db: AsyncSession) -> DocumentChunk:
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = result.scalar_one_or_none()
            if not chunk:
                raise HTTPException(status_code=404, detail="Chunk not found")
            return chunk
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving chunk: {str(e)}")

    @staticmethod
    async def list_chunks_by_file(file_id: UUID, db: AsyncSession) -> List[DocumentChunk]:
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.file_id == file_id))
            chunks = result.scalars().all()
            return chunks
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Error listing chunks: {str(e)}")

    @staticmethod
    async def update_chunk(chunk_id: UUID, chunk_update: BaseModel, db: AsyncSession):
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = result.scalar_one_or_none()
            if not chunk:
                raise HTTPException(status_code=404, detail="Chunk not found")

            for key, value in chunk_update.dict(exclude_unset=True).items():
                setattr(chunk, key, value)

            db.add(chunk)
            await db.commit()
            return chunk
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Error updating chunk: {str(e)}")

    @staticmethod
    async def delete_chunk(chunk_id: UUID, db: AsyncSession):
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = result.scalar_one_or_none()
            if not chunk:
                raise HTTPException(status_code=404, detail="Chunk not found")

            await db.delete(chunk)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Error deleting chunk: {str(e)}")