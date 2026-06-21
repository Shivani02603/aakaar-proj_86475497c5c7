from uuid import UUID
from typing import List, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from database.models import Session, UploadedFile, Message
from database.models import DocumentChunk
from sqlalchemy.orm import joinedload


class FrontendService:
    async def create_session(self, user_id: UUID, name: str, db: AsyncSession) -> Session:
        try:
            new_session = Session(
                id=UUID(),
                user_id=user_id,
                name=name,
                created_at=datetime.utcnow(),
            )
            db.add(new_session)
            await db.commit()
            await db.refresh(new_session)
            return new_session
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create session due to integrity error.",
            )

    async def get_session_by_id(self, session_id: UUID, db: AsyncSession) -> Session:
        result = await db.execute(select(Session).where(Session.id == session_id))
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with ID {session_id} not found.",
            )
        return session

    async def list_sessions(self, user_id: UUID, db: AsyncSession) -> List[Session]:
        result = await db.execute(select(Session).where(Session.user_id == user_id))
        sessions = result.scalars().all()
        return sessions

    async def update_session(self, session_id: UUID, name: str, db: AsyncSession) -> Session:
        result = await db.execute(select(Session).where(Session.id == session_id))
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with ID {session_id} not found.",
            )
        session.name = name
        await db.commit()
        await db.refresh(session)
        return session

    async def delete_session(self, session_id: UUID, db: AsyncSession) -> None:
        result = await db.execute(select(Session).where(Session.id == session_id))
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with ID {session_id} not found.",
            )
        await db.delete(session)
        await db.commit()

    async def list_files_by_session(self, session_id: UUID, db: AsyncSession) -> List[UploadedFile]:
        result = await db.execute(select(UploadedFile).where(UploadedFile.session_id == session_id))
        files = result.scalars().all()
        return files

    async def get_messages_by_session(self, session_id: UUID, db: AsyncSession) -> List[Message]:
        result = await db.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at.asc())
        )
        messages = result.scalars().all()
        return messages

    async def get_citations_for_message(self, message_id: UUID, db: AsyncSession) -> List[Dict[str, Any]]:
        result = await db.execute(
            select(DocumentChunk)
            .join(Message, DocumentChunk.file_id == Message.id)
            .where(Message.id == message_id)
        )
        chunks = result.scalars().all()
        citations = [
            {
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "metadata": chunk.metadata,
            }
            for chunk in chunks
        ]
        return citations