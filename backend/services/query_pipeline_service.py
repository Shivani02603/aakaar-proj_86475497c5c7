import os
from uuid import UUID
from typing import List, Dict, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from database.models import DocumentChunk, UploadedFile, Message
from ai.embeddings import embed_query
from ai.vector_store import VectorStore
from ai.rag import retrieve_context, answer_question
from env import GOOGLE_GEMINI_API_KEY

class QueryPipelineService:
    def __init__(self):
        self.vector_store = VectorStore()

    async def embed_query(self, query: str) -> List[float]:
        try:
            embedding = embed_query(query)
            return embedding
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to embed query: {str(e)}"
            )

    async def retrieve_top_chunks(self, query_embedding: List[float], top_k: int, db: AsyncSession) -> List[Dict]:
        try:
            chunks = self.vector_store.search(query_embedding, top_k)
            if not chunks:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No relevant chunks found."
                )
            return chunks
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve top chunks: {str(e)}"
            )

    async def generate_answer(
        self, query: str, context: List[Dict], session_id: UUID, user_id: UUID, db: AsyncSession
    ) -> Dict:
        if not GOOGLE_GEMINI_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google Gemini API key not configured."
            )

        try:
            answer_data = answer_question(query=query, context=context, session_id=session_id, user_id=user_id)
            if not answer_data.get("answer") or not answer_data.get("citations"):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to generate answer or retrieve citations."
                )
            return answer_data
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate answer: {str(e)}"
            )

    async def save_messages(
        self, session_id: UUID, user_message: str, assistant_message: str, citations: List[Dict], db: AsyncSession
    ):
        try:
            user_message_entry = Message(
                session_id=session_id,
                role="user",
                content=user_message,
                metadata={},
            )
            assistant_message_entry = Message(
                session_id=session_id,
                role="assistant",
                content=assistant_message,
                metadata={"citations": citations},
            )
            db.add(user_message_entry)
            db.add(assistant_message_entry)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save messages: {str(e)}"
            )

    async def query_pipeline(
        self, query: str, session_id: UUID, user_id: UUID, top_k: int, db: AsyncSession
    ) -> Dict:
        try:
            # Step 1: Embed the query
            query_embedding = await self.embed_query(query)

            # Step 2: Retrieve top chunks
            top_chunks = await self.retrieve_top_chunks(query_embedding, top_k, db)

            # Step 3: Generate answer using context
            answer_data = await self.generate_answer(query, top_chunks, session_id, user_id, db)

            # Step 4: Save user and assistant messages
            await self.save_messages(
                session_id=session_id,
                user_message=query,
                assistant_message=answer_data["answer"],
                citations=answer_data["citations"],
                db=db,
            )

            return answer_data
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Query pipeline failed: {str(e)}"
            )

    async def create_chunk(self, chunk: DocumentChunk, db: AsyncSession):
        try:
            db.add(chunk)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create chunk: {str(e)}"
            )

    async def get_chunk_by_id(self, chunk_id: UUID, db: AsyncSession) -> DocumentChunk:
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = result.scalar_one_or_none()
            if not chunk:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Chunk not found."
                )
            return chunk
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve chunk: {str(e)}"
            )

    async def list_all_chunks(self, db: AsyncSession) -> List[DocumentChunk]:
        try:
            result = await db.execute(select(DocumentChunk))
            chunks = result.scalars().all()
            return chunks
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list chunks: {str(e)}"
            )

    async def update_chunk(self, chunk_id: UUID, chunk_update: Dict, db: AsyncSession):
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = result.scalar_one_or_none()
            if not chunk:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Chunk not found."
                )
            for key, value in chunk_update.items():
                setattr(chunk, key, value)
            db.add(chunk)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update chunk: {str(e)}"
            )

    async def delete_chunk(self, chunk_id: UUID, db: AsyncSession):
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = result.scalar_one_or_none()
            if not chunk:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Chunk not found."
                )
            await db.delete(chunk)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete chunk: {str(e)}"
            )