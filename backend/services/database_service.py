import os
from uuid import UUID
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from database.models import User, Session, UploadedFile, DocumentChunk, Message
from sqlalchemy.orm import joinedload


class DatabaseService:
    @staticmethod
    async def create_user(user: User, db: AsyncSession) -> User:
        try:
            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating user: {str(e)}"
            )

    @staticmethod
    async def get_user_by_id(user_id: UUID, db: AsyncSession) -> User:
        try:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            return user
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving user: {str(e)}"
            )

    @staticmethod
    async def list_users(db: AsyncSession) -> List[User]:
        try:
            result = await db.execute(select(User))
            users = result.scalars().all()
            return users
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error listing users: {str(e)}"
            )

    @staticmethod
    async def update_user(user_id: UUID, user_update: dict, db: AsyncSession) -> User:
        try:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            for key, value in user_update.items():
                setattr(user, key, value)
            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating user: {str(e)}"
            )

    @staticmethod
    async def delete_user(user_id: UUID, db: AsyncSession) -> None:
        try:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            await db.delete(user)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting user: {str(e)}"
            )

    @staticmethod
    async def create_session(session: Session, db: AsyncSession) -> Session:
        try:
            db.add(session)
            await db.commit()
            await db.refresh(session)
            return session
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating session: {str(e)}"
            )

    @staticmethod
    async def get_session_by_id(session_id: UUID, db: AsyncSession) -> Session:
        try:
            result = await db.execute(select(Session).where(Session.id == session_id))
            session = result.scalar_one_or_none()
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Session not found"
                )
            return session
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving session: {str(e)}"
            )

    @staticmethod
    async def list_sessions(db: AsyncSession) -> List[Session]:
        try:
            result = await db.execute(select(Session))
            sessions = result.scalars().all()
            return sessions
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error listing sessions: {str(e)}"
            )

    @staticmethod
    async def update_session(session_id: UUID, session_update: dict, db: AsyncSession) -> Session:
        try:
            result = await db.execute(select(Session).where(Session.id == session_id))
            session = result.scalar_one_or_none()
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Session not found"
                )
            for key, value in session_update.items():
                setattr(session, key, value)
            db.add(session)
            await db.commit()
            await db.refresh(session)
            return session
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating session: {str(e)}"
            )

    @staticmethod
    async def delete_session(session_id: UUID, db: AsyncSession) -> None:
        try:
            result = await db.execute(select(Session).where(Session.id == session_id))
            session = result.scalar_one_or_none()
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Session not found"
                )
            await db.delete(session)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting session: {str(e)}"
            )

    @staticmethod
    async def create_uploaded_file(file: UploadedFile, db: AsyncSession) -> UploadedFile:
        try:
            db.add(file)
            await db.commit()
            await db.refresh(file)
            return file
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating uploaded file: {str(e)}"
            )

    @staticmethod
    async def get_uploaded_file_by_id(file_id: UUID, db: AsyncSession) -> UploadedFile:
        try:
            result = await db.execute(select(UploadedFile).where(UploadedFile.id == file_id))
            file = result.scalar_one_or_none()
            if not file:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Uploaded file not found"
                )
            return file
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving uploaded file: {str(e)}"
            )

    @staticmethod
    async def list_uploaded_files(db: AsyncSession) -> List[UploadedFile]:
        try:
            result = await db.execute(select(UploadedFile))
            files = result.scalars().all()
            return files
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error listing uploaded files: {str(e)}"
            )

    @staticmethod
    async def update_uploaded_file(file_id: UUID, file_update: dict, db: AsyncSession) -> UploadedFile:
        try:
            result = await db.execute(select(UploadedFile).where(UploadedFile.id == file_id))
            file = result.scalar_one_or_none()
            if not file:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Uploaded file not found"
                )
            for key, value in file_update.items():
                setattr(file, key, value)
            db.add(file)
            await db.commit()
            await db.refresh(file)
            return file
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating uploaded file: {str(e)}"
            )

    @staticmethod
    async def delete_uploaded_file(file_id: UUID, db: AsyncSession) -> None:
        try:
            result = await db.execute(select(UploadedFile).where(UploadedFile.id == file_id))
            file = result.scalar_one_or_none()
            if not file:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Uploaded file not found"
                )
            await db.delete(file)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting uploaded file: {str(e)}"
            )