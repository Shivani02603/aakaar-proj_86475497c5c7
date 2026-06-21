from uuid import UUID
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from database.models import User, Session, UploadedFile, DocumentChunk, Message


class DatabaseService:
    async def create_user(self, email: str, db: AsyncSession) -> User:
        try:
            new_user = User(id=UUID(), email=email, created_at=datetime.utcnow())
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            return new_user
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists.",
            )

    async def get_user_by_id(self, user_id: UUID, db: AsyncSession) -> User:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
        return user

    async def list_users(self, db: AsyncSession) -> List[User]:
        result = await db.execute(select(User))
        users = result.scalars().all()
        return users

    async def update_user(self, user_id: UUID, email: Optional[str], db: AsyncSession) -> User:
        user = await self.get_user_by_id(user_id, db)
        if email:
            user.email = email
        user.updated_at = datetime.utcnow()
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def delete_user(self, user_id: UUID, db: AsyncSession) -> None:
        user = await self.get_user_by_id(user_id, db)
        await db.delete(user)
        await db.commit()

    async def create_session(self, user_id: UUID, name: str, db: AsyncSession) -> Session:
        try:
            new_session = Session(id=UUID(), user_id=user_id, name=name, created_at=datetime.utcnow())
            db.add(new_session)
            await db.commit()
            await db.refresh(new_session)
            return new_session
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session creation failed.",
            )

    async def get_session_by_id(self, session_id: UUID, db: AsyncSession) -> Session:
        result = await db.execute(select(Session).where(Session.id == session_id))
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found.",
            )
        return session

    async def list_sessions(self, db: AsyncSession) -> List[Session]:
        result = await db.execute(select(Session))
        sessions = result.scalars().all()
        return sessions

    async def update_session(self, session_id: UUID, name: Optional[str], db: AsyncSession) -> Session:
        session = await self.get_session_by_id(session_id, db)
        if name:
            session.name = name
        session.updated_at = datetime.utcnow()
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    async def delete_session(self, session_id: UUID, db: AsyncSession) -> None:
        session = await self.get_session_by_id(session_id, db)
        await db.delete(session)
        await db.commit()

    async def create_uploaded_file(
        self, session_id: UUID, filename: str, original_filename: str, file_size: int, status: str, db: AsyncSession
    ) -> UploadedFile:
        try:
            new_file = UploadedFile(
                id=UUID(),
                session_id=session_id,
                filename=filename,
                original_filename=original_filename,
                file_size=file_size,
                status=status,
                uploaded_at=datetime.utcnow(),
            )
            db.add(new_file)
            await db.commit()
            await db.refresh(new_file)
            return new_file
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File upload failed.",
            )

    async def get_uploaded_file_by_id(self, file_id: UUID, db: AsyncSession) -> UploadedFile:
        result = await db.execute(select(UploadedFile).where(UploadedFile.id == file_id))
        file = result.scalar_one_or_none()
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Uploaded file not found.",
            )
        return file

    async def list_uploaded_files(self, session_id: UUID, db: AsyncSession) -> List[UploadedFile]:
        result = await db.execute(select(UploadedFile).where(UploadedFile.session_id == session_id))
        files = result.scalars().all()
        return files

    async def update_uploaded_file_status(self, file_id: UUID, status: str, db: AsyncSession) -> UploadedFile:
        file = await self.get_uploaded_file_by_id(file_id, db)
        file.status = status
        file.updated_at = datetime.utcnow()
        db.add(file)
        await db.commit()
        await db.refresh(file)
        return file

    async def delete_uploaded_file(self, file_id: UUID, db: AsyncSession) -> None:
        file = await self.get_uploaded_file_by_id(file_id, db)
        await db.delete(file)
        await db.commit()

    async def create_document_chunk(
        self, file_id: UUID, content: str, embedding: List[float], metadata: dict, chunk_index: int, db: AsyncSession
    ) -> DocumentChunk:
        try:
            new_chunk = DocumentChunk(
                id=UUID(),
                file_id=file_id,
                content=content,
                embedding=embedding,
                metadata=metadata,
                chunk_index=chunk_index,
                created_at=datetime.utcnow(),
            )
            db.add(new_chunk)
            await db.commit()
            await db.refresh(new_chunk)
            return new_chunk
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document chunk creation failed.",
            )

    async def get_document_chunk_by_id(self, chunk_id: UUID, db: AsyncSession) -> DocumentChunk:
        result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
        chunk = result.scalar_one_or_none()
        if not chunk:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document chunk not found.",
            )
        return chunk

    async def list_document_chunks(self, file_id: UUID, db: AsyncSession) -> List[DocumentChunk]:
        result = await db.execute(select(DocumentChunk).where(DocumentChunk.file_id == file_id))
        chunks = result.scalars().all()
        return chunks

    async def delete_document_chunk(self, chunk_id: UUID, db: AsyncSession) -> None:
        chunk = await self.get_document_chunk_by_id(chunk_id, db)
        await db.delete(chunk)
        await db.commit()

    async def create_message(
        self, session_id: UUID, role: str, content: str, metadata: dict, db: AsyncSession
    ) -> Message:
        try:
            new_message = Message(
                id=UUID(),
                session_id=session_id,
                role=role,
                content=content,
                metadata=metadata,
                created_at=datetime.utcnow(),
            )
            db.add(new_message)
            await db.commit()
            await db.refresh(new_message)
            return new_message
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message creation failed.",
            )

    async def get_message_by_id(self, message_id: UUID, db: AsyncSession) -> Message:
        result = await db.execute(select(Message).where(Message.id == message_id))
        message = result.scalar_one_or_none()
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found.",
            )
        return message

    async def list_messages(self, session_id: UUID, db: AsyncSession) -> List[Message]:
        result = await db.execute(select(Message).where(Message.session_id == session_id))
        messages = result.scalars().all()
        return messages

    async def delete_message(self, message_id: UUID, db: AsyncSession) -> None:
        message = await self.get_message_by_id(message_id, db)
        await db.delete(message)
        await db.commit()