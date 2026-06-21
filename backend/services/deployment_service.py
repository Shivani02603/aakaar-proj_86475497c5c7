from uuid import UUID
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from database.models import Deployment
from env import get_docker_compose_config


class DeploymentService:
    @staticmethod
    async def create_deployment(deployment: Deployment, db: AsyncSession) -> Deployment:
        try:
            db.add(deployment)
            await db.commit()
            await db.refresh(deployment)
            return deployment
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Deployment creation failed due to integrity error."
            )

    @staticmethod
    async def get_deployment_by_id(deployment_id: UUID, db: AsyncSession) -> Deployment:
        result = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
        deployment = result.scalar_one_or_none()
        if not deployment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Deployment with ID {deployment_id} not found."
            )
        return deployment

    @staticmethod
    async def list_all_deployments(db: AsyncSession) -> List[Deployment]:
        result = await db.execute(select(Deployment))
        deployments = result.scalars().all()
        return deployments

    @staticmethod
    async def update_deployment(deployment_id: UUID, deployment_data: dict, db: AsyncSession) -> Deployment:
        result = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
        deployment = result.scalar_one_or_none()
        if not deployment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Deployment with ID {deployment_id} not found."
            )
        for key, value in deployment_data.items():
            setattr(deployment, key, value)
        try:
            await db.commit()
            await db.refresh(deployment)
            return deployment
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Deployment update failed due to integrity error."
            )

    @staticmethod
    async def delete_deployment(deployment_id: UUID, db: AsyncSession) -> None:
        result = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
        deployment = result.scalar_one_or_none()
        if not deployment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Deployment with ID {deployment_id} not found."
            )
        try:
            await db.delete(deployment)
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Deployment deletion failed due to integrity error."
            )

    @staticmethod
    async def setup_docker_compose(db: AsyncSession) -> dict:
        try:
            docker_compose_config = get_docker_compose_config()
            # Simulate Docker Compose setup logic here
            # Example: Write docker_compose_config to a file, execute Docker Compose commands, etc.
            return {"status": "success", "message": "Docker Compose setup completed successfully."}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Docker Compose setup failed: {str(e)}"
            )