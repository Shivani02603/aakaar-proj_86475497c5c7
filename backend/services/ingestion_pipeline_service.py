from uuid import UUID
from typing import List, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import pandas as pd
from openai import OpenAI
from database.models import DocumentChunk, UploadedFile
from backend.routers.ingestion_pipeline import chunk_text
from ai.embeddings import embed_batch

class IngestionPipelineService:
    @staticmethod
    async def create_chunks_from_excel(file_id: UUID, db: AsyncSession) -> List[DocumentChunk]:
        try:
            # Fetch the file record
            file_record = await db.execute(select(UploadedFile).where(UploadedFile.id == file_id))
            file = file_record.scalar_one_or_none()
            if not file:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

            # Load the Excel file
            file_path = file.filename
            try:
                df = pd.read_excel(file_path)
            except Exception as e:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error reading Excel file: {str(e)}")

            # Combine all text content from the Excel file
            content = " ".join(df.astype(str).apply(lambda x: " ".join(x), axis=1))

            # Chunk the content
            chunks = chunk_text(content, chunk_size=1000, overlap=200)

            # Embed the chunks
            embeddings = embed_batch(chunks)

            # Store chunks in the database
            document_chunks = []
            for index, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                document_chunk = DocumentChunk(
                    id=UUID(),
                    file_id=file_id,
                    content=chunk,
                    embedding=embedding,
                    metadata={"source": file.original_filename},
                    chunk_index=index,
                    created_at=datetime.utcnow()
                )
                db.add(document_chunk)
                document_chunks.append(document_chunk)

            await db.commit()
            return document_chunks
        except IntegrityError as e:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error: {str(e)}")

    @staticmethod
    async def get_chunk_by_id(chunk_id: UUID, db: AsyncSession) -> DocumentChunk:
        try:
            chunk_record = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = chunk_record.scalar_one_or_none()
            if not chunk:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chunk not found")
            return chunk
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error: {str(e)}")

    @staticmethod
    async def list_chunks_by_file(file_id: UUID, db: AsyncSession) -> List[DocumentChunk]:
        try:
            chunks_record = await db.execute(select(DocumentChunk).where(DocumentChunk.file_id == file_id))
            chunks = chunks_record.scalars().all()
            if not chunks:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No chunks found for the file")
            return chunks
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error: {str(e)}")

    @staticmethod
    async def update_chunk(chunk_id: UUID, chunk_update: Dict[str, Any], db: AsyncSession) -> DocumentChunk:
        try:
            chunk_record = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = chunk_record.scalar_one_or_none()
            if not chunk:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chunk not found")

            for key, value in chunk_update.items():
                setattr(chunk, key, value)

            chunk.updated_at = datetime.utcnow()
            db.add(chunk)
            await db.commit()
            return chunk
        except IntegrityError as e:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error: {str(e)}")

    @staticmethod
    async def delete_chunk(chunk_id: UUID, db: AsyncSession) -> None:
        try:
            chunk_record = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = chunk_record.scalar_one_or_none()
            if not chunk:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chunk not found")

            await db.delete(chunk)
            await db.commit()
        except IntegrityError as e:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error: {str(e)}")