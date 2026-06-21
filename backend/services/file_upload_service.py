import os
from uuid import UUID
from typing import List
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from database.models import UploadedFile
from env import UPLOAD_DIRECTORY

class FileUploadService:
    @staticmethod
    async def create_file(file: UploadedFile, db: AsyncSession) -> UploadedFile:
        try:
            db.add(file)
            await db.commit()
            await db.refresh(file)
            return file
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating file record: {str(e)}"
            )

    @staticmethod
    async def get_file_by_id(file_id: UUID, db: AsyncSession) -> UploadedFile:
        try:
            result = await db.execute(select(UploadedFile).where(UploadedFile.id == file_id))
            file = result.scalar_one_or_none()
            if not file:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"File with ID {file_id} not found"
                )
            return file
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving file: {str(e)}"
            )

    @staticmethod
    async def list_files(db: AsyncSession) -> List[UploadedFile]:
        try:
            result = await db.execute(select(UploadedFile))
            files = result.scalars().all()
            return files
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error listing files: {str(e)}"
            )

    @staticmethod
    async def update_file(file_id: UUID, file_update: dict, db: AsyncSession) -> UploadedFile:
        try:
            result = await db.execute(select(UploadedFile).where(UploadedFile.id == file_id))
            file = result.scalar_one_or_none()
            if not file:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"File with ID {file_id} not found"
                )
            for key, value in file_update.items():
                setattr(file, key, value)
            await db.commit()
            await db.refresh(file)
            return file
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating file: {str(e)}"
            )

    @staticmethod
    async def delete_file(file_id: UUID, db: AsyncSession) -> None:
        try:
            result = await db.execute(select(UploadedFile).where(UploadedFile.id == file_id))
            file = result.scalar_one_or_none()
            if not file:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"File with ID {file_id} not found"
                )
            await db.delete(file)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting file: {str(e)}"
            )

    @staticmethod
    async def save_uploaded_file(upload_file: UploadFile, session_id: UUID, db: AsyncSession) -> UploadedFile:
        try:
            # Validate file type
            if not upload_file.filename.endswith(".xlsx"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only Excel (.xlsx) files are allowed"
                )

            # Save file to disk
            file_path = os.path.join(UPLOAD_DIRECTORY, upload_file.filename)
            with open(file_path, "wb") as file:
                file.write(await upload_file.read())

            # Create file record in database
            file_record = UploadedFile(
                session_id=session_id,
                filename=upload_file.filename,
                original_filename=upload_file.filename,
                file_size=os.path.getsize(file_path),
                status="uploaded"
            )
            return await FileUploadService.create_file(file_record, db)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error saving uploaded file: {str(e)}"
            )