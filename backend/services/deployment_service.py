import os
from uuid import UUID
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from database.models import Deployment
from pydantic import BaseModel


class DeploymentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    config: dict


class DeploymentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[dict]


class DeploymentResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    config: dict


class DeploymentService:
    @staticmethod
    async def create_deployment(deployment_data: DeploymentCreate, db: AsyncSession) -> DeploymentResponse:
        try:
            new_deployment = Deployment(
                name=deployment_data.name,
                description=deployment_data.description,
                config=deployment_data.config,
            )
            db.add(new_deployment)
            await db.commit()
            await db.refresh(new_deployment)
            return DeploymentResponse(
                id=new_deployment.id,
                name=new_deployment.name,
                description=new_deployment.description,
                config=new_deployment.config,
            )
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating deployment: {str(e)}",
            )

    @staticmethod
    async def get_deployment_by_id(deployment_id: UUID, db: AsyncSession) -> DeploymentResponse:
        try:
            result = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
            deployment = result.scalar_one_or_none()
            if not deployment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Deployment with ID {deployment_id} not found.",
                )
            return DeploymentResponse(
                id=deployment.id,
                name=deployment.name,
                description=deployment.description,
                config=deployment.config,
            )
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving deployment: {str(e)}",
            )

    @staticmethod
    async def list_all_deployments(db: AsyncSession) -> List[DeploymentResponse]:
        try:
            result = await db.execute(select(Deployment))
            deployments = result.scalars().all()
            return [
                DeploymentResponse(
                    id=deployment.id,
                    name=deployment.name,
                    description=deployment.description,
                    config=deployment.config,
                )
                for deployment in deployments
            ]
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error listing deployments: {str(e)}",
            )

    @staticmethod
    async def update_deployment(deployment_id: UUID, deployment_update: DeploymentUpdate, db: AsyncSession) -> DeploymentResponse:
        try:
            result = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
            deployment = result.scalar_one_or_none()
            if not deployment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Deployment with ID {deployment_id} not found.",
                )
            if deployment_update.name is not None:
                deployment.name = deployment_update.name
            if deployment_update.description is not None:
                deployment.description = deployment_update.description
            if deployment_update.config is not None:
                deployment.config = deployment_update.config
            await db.commit()
            await db.refresh(deployment)
            return DeploymentResponse(
                id=deployment.id,
                name=deployment.name,
                description=deployment.description,
                config=deployment.config,
            )
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating deployment: {str(e)}",
            )

    @staticmethod
    async def delete_deployment(deployment_id: UUID, db: AsyncSession) -> None:
        try:
            result = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
            deployment = result.scalar_one_or_none()
            if not deployment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Deployment with ID {deployment_id} not found.",
                )
            await db.delete(deployment)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting deployment: {str(e)}",
            )

    @staticmethod
    async def setup_docker_compose(db: AsyncSession) -> dict:
        try:
            # Example Docker Compose setup logic
            backend_service = {
                "image": "backend:latest",
                "ports": ["8000:8000"],
                "environment": ["DATABASE_URL=postgresql://user:password@db:5432/app"],
            }
            frontend_service = {
                "image": "frontend:latest",
                "ports": ["3000:3000"],
            }
            db_service = {
                "image": "postgres:latest",
                "ports": ["5432:5432"],
                "environment": ["POSTGRES_USER=user", "POSTGRES_PASSWORD=password", "POSTGRES_DB=app"],
            }
            docker_compose_config = {
                "version": "3.8",
                "services": {
                    "backend": backend_service,
                    "frontend": frontend_service,
                    "db": db_service,
                },
            }
            return docker_compose_config
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error setting up Docker Compose: {str(e)}",
            )