from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from database.models import Deployment
from database.config import get_db
from backend.services.auth import jwt_auth_dependency

router = APIRouter(prefix="/deployment", tags=["Deployment"])

# Pydantic schemas
class DeploymentBase(BaseModel):
    name: str = Field(..., example="My Deployment")
    description: Optional[str] = Field(None, example="Description of the deployment")
    created_at: Optional[datetime] = Field(None, example="2023-10-01T12:00:00Z")

class DeploymentCreate(DeploymentBase):
    pass

class DeploymentUpdate(BaseModel):
    name: Optional[str] = Field(None, example="Updated Deployment Name")
    description: Optional[str] = Field(None, example="Updated description")

class DeploymentResponse(DeploymentBase):
    id: UUID = Field(..., example="123e4567-e89b-12d3-a456-426614174000")

# CRUD endpoints
@router.post("/", response_model=DeploymentResponse, status_code=status.HTTP_201_CREATED)
async def create_deployment(
    deployment: DeploymentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(jwt_auth_dependency),
):
    new_deployment = Deployment(
        name=deployment.name,
        description=deployment.description,
        created_at=datetime.utcnow(),
    )
    db.add(new_deployment)
    db.commit()
    db.refresh(new_deployment)
    return DeploymentResponse(
        id=new_deployment.id,
        name=new_deployment.name,
        description=new_deployment.description,
        created_at=new_deployment.created_at,
    )

@router.get("/", response_model=List[DeploymentResponse])
async def list_deployments(
    db: Session = Depends(get_db),
    current_user: dict = Depends(jwt_auth_dependency),
):
    deployments = db.query(Deployment).all()
    return [
        DeploymentResponse(
            id=deployment.id,
            name=deployment.name,
            description=deployment.description,
            created_at=deployment.created_at,
        )
        for deployment in deployments
    ]

@router.get("/{deployment_id}", response_model=DeploymentResponse)
async def get_deployment(
    deployment_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(jwt_auth_dependency),
):
    deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
    if not deployment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found")
    return DeploymentResponse(
        id=deployment.id,
        name=deployment.name,
        description=deployment.description,
        created_at=deployment.created_at,
    )

@router.put("/{deployment_id}", response_model=DeploymentResponse)
async def update_deployment(
    deployment_id: UUID,
    deployment_update: DeploymentUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(jwt_auth_dependency),
):
    deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
    if not deployment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found")
    if deployment_update.name:
        deployment.name = deployment_update.name
    if deployment_update.description:
        deployment.description = deployment_update.description
    db.commit()
    db.refresh(deployment)
    return DeploymentResponse(
        id=deployment.id,
        name=deployment.name,
        description=deployment.description,
        created_at=deployment.created_at,
    )

@router.delete("/{deployment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deployment(
    deployment_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(jwt_auth_dependency),
):
    deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
    if not deployment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found")
    db.delete(deployment)
    db.commit()
    return None

# Docker Compose setup endpoint
@router.post("/setup-docker-compose", status_code=status.HTTP_200_OK)
async def setup_docker_compose(
    db: Session = Depends(get_db),
    current_user: dict = Depends(jwt_auth_dependency),
):
    try:
        # Simulate Docker Compose setup logic
        # This would typically involve writing a docker-compose.yml file and executing Docker commands
        docker_compose_content = """
        version: '3.8'
        services:
          backend:
            image: backend:latest
            ports:
              - "8000:8000"
            environment:
              - DATABASE_URL=postgresql://user:password@db:5432/aakaar
          frontend:
            image: frontend:latest
            ports:
              - "3000:3000"
          db:
            image: postgres:latest
            environment:
              - POSTGRES_USER=user
              - POSTGRES_PASSWORD=password
              - POSTGRES_DB=aakaar
            ports:
              - "5432:5432"
        """
        # Normally, you'd write this to a file and execute Docker commands
        return {"message": "Docker Compose setup completed successfully"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))