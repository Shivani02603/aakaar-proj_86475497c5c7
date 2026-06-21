from uuid import UUID
from typing import List, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from database.models import DocumentChunk
from ai.embeddings import embed_query
from ai.vector_store import retrieve_top_chunks
from backend.routers.query_pipeline import build_prompt_context, call_llm


class QueryPipelineService:
    async def embed_query(self, query: str) -> List[float]:
        """
        Embed the user query into a vector representation.
        """
        try:
            embedding = embed_query(query)
            return embedding
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to embed query: {str(e)}"
            )

    async def retrieve_top_chunks(self, query_embedding: List[float], top_k: int, db: AsyncSession) -> List[DocumentChunk]:
        """
        Retrieve the top-k chunks based on cosine similarity using pgvector.
        """
        try:
            chunks = retrieve_top_chunks(query_embedding, top_k, db)
            if not chunks:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No relevant chunks found for the query."
                )
            return chunks
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve top chunks: {str(e)}"
            )

    async def generate_answer(self, query: str, chunks: List[DocumentChunk]) -> Dict[str, Any]:
        """
        Generate an answer using the retrieved context and the user's query.
        """
        try:
            context = build_prompt_context(chunks)
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": query},
                {"role": "assistant", "content": context}
            ]
            answer = call_llm(messages, stream=False)
            return answer
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate answer: {str(e)}"
            )

    async def query_pipeline(self, query: str, top_k: int, db: AsyncSession) -> Dict[str, Any]:
        """
        Execute the full query pipeline: embed query, retrieve top chunks, and generate answer.
        """
        try:
            # Step 1: Embed the query
            query_embedding = await self.embed_query(query)

            # Step 2: Retrieve top-k chunks
            chunks = await self.retrieve_top_chunks(query_embedding, top_k, db)

            # Step 3: Generate the answer
            answer = await self.generate_answer(query, chunks)

            # Step 4: Include citations in the response
            citations = [
                {
                    "filename": chunk.metadata.get("filename"),
                    "row_range": chunk.metadata.get("row_range")
                }
                for chunk in chunks
            ]
            return {
                "answer": answer,
                "citations": citations
            }
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to execute query pipeline: {str(e)}"
            )

    async def create_chunk(self, chunk_data: Dict[str, Any], db: AsyncSession) -> DocumentChunk:
        """
        Create a new document chunk in the database.
        """
        try:
            new_chunk = DocumentChunk(**chunk_data)
            db.add(new_chunk)
            await db.commit()
            await db.refresh(new_chunk)
            return new_chunk
        except IntegrityError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create chunk: {str(e)}"
            )

    async def get_chunk_by_id(self, chunk_id: UUID, db: AsyncSession) -> DocumentChunk:
        """
        Retrieve a document chunk by its ID.
        """
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = result.scalar_one_or_none()
            if not chunk:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Chunk not found."
                )
            return chunk
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve chunk: {str(e)}"
            )

    async def list_all_chunks(self, db: AsyncSession) -> List[DocumentChunk]:
        """
        List all document chunks in the database.
        """
        try:
            result = await db.execute(select(DocumentChunk))
            chunks = result.scalars().all()
            return chunks
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list chunks: {str(e)}"
            )

    async def update_chunk(self, chunk_id: UUID, update_data: Dict[str, Any], db: AsyncSession) -> DocumentChunk:
        """
        Update a document chunk by its ID.
        """
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = result.scalar_one_or_none()
            if not chunk:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Chunk not found."
                )
            for key, value in update_data.items():
                setattr(chunk, key, value)
            db.add(chunk)
            await db.commit()
            await db.refresh(chunk)
            return chunk
        except IntegrityError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to update chunk: {str(e)}"
            )

    async def delete_chunk(self, chunk_id: UUID, db: AsyncSession) -> None:
        """
        Delete a document chunk by its ID.
        """
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
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete chunk: {str(e)}"
            )