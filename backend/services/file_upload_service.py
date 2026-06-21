from uuid import UUID
from typing import List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from database.models import UploadedFile
from datetime import datetime


class FileUploadService:
    @staticmethod
    async def create_file(
        session_id: UUID,
        filename: str,
        original_filename: str,
        file_size: int,
        status: str,
        uploaded_at: datetime,
        db: AsyncSession,
    ) -> UploadedFile:
        try:
            new_file = UploadedFile(
                session_id=session_id,
                filename=filename,
                original_filename=original_filename,
                file_size=file_size,
                status=status,
                uploaded_at=uploaded_at,
            )
            db.add(new_file)
            await db.commit()
            await db.refresh(new_file)
            return new_file
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create file due to integrity error.",
            )

    @staticmethod
    async def get_file_by_id(file_id: UUID, db: AsyncSession) -> UploadedFile:
        result = await db.execute(select(UploadedFile).where(UploadedFile.id == file_id))
        file = result.scalar_one_or_none()
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File with ID {file_id} not found.",
            )
        return file

    @staticmethod
    async def list_files(session_id: UUID, db: AsyncSession) -> List[UploadedFile]:
        result = await db.execute(select(UploadedFile).where(UploadedFile.session_id == session_id))
        files = result.scalars().all()
        return files

    @staticmethod
    async def update_file_status(file_id: UUID, status: str, db: AsyncSession) -> UploadedFile:
        file = await FileUploadService.get_file_by_id(file_id, db)
        file.status = status
        try:
            db.add(file)
            await db.commit()
            await db.refresh(file)
            return file
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update file status due to integrity error.",
            )

    @staticmethod
    async def delete_file(file_id: UUID, db: AsyncSession) -> None:
        file = await FileUploadService.get_file_by_id(file_id, db)
        try:
            await db.delete(file)
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to delete file due to integrity error.",
            )