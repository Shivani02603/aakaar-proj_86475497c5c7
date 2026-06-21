from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from database.models import Deployment
from database.config import get_db
from backend.services.auth import get_current_user

router = APIRouter(prefix="/deployment", tags=["Deployment"])

# Pydantic schemas
class DeploymentBase(BaseModel):
    name: str = Field(..., example="My Deployment")
    description: Optional[str] = Field(None, example="Deployment description")
    backend_image: str = Field(..., example="backend:latest")
    frontend_image: str = Field(..., example="frontend:latest")
    database_image: str = Field(..., example="postgres:latest")

class DeploymentCreate(DeploymentBase):
    pass

class DeploymentUpdate(BaseModel):
    name: Optional[str] = Field(None, example="Updated Deployment Name")
    description: Optional[str] = Field(None, example="Updated Deployment description")
    backend_image: Optional[str] = Field(None, example="backend:latest")
    frontend_image: Optional[str] = Field(None, example="frontend:latest")
    database_image: Optional[str] = Field(None, example="postgres:latest")

class DeploymentResponse(DeploymentBase):
    id: UUID
    created_at: str

# CRUD endpoints
@router.post("/", response_model=DeploymentResponse, status_code=status.HTTP_201_CREATED)
async def create_deployment_endpoint(
    deployment: DeploymentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    new_deployment = Deployment(**deployment.dict())
    db.add(new_deployment)
    db.commit()
    db.refresh(new_deployment)
    return DeploymentResponse(
        id=new_deployment.id,
        name=new_deployment.name,
        description=new_deployment.description,
        backend_image=new_deployment.backend_image,
        frontend_image=new_deployment.frontend_image,
        database_image=new_deployment.database_image,
        created_at=new_deployment.created_at.isoformat(),
    )

@router.get("/", response_model=List[DeploymentResponse])
async def list_deployments_endpoint(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    deployments = db.query(Deployment).all()
    return [
        DeploymentResponse(
            id=deployment.id,
            name=deployment.name,
            description=deployment.description,
            backend_image=deployment.backend_image,
            frontend_image=deployment.frontend_image,
            database_image=deployment.database_image,
            created_at=deployment.created_at.isoformat(),
        )
        for deployment in deployments
    ]

@router.get("/{deployment_id}", response_model=DeploymentResponse)
async def get_deployment_endpoint(
    deployment_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
    if not deployment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found")
    return DeploymentResponse(
        id=deployment.id,
        name=deployment.name,
        description=deployment.description,
        backend_image=deployment.backend_image,
        frontend_image=deployment.frontend_image,
        database_image=deployment.database_image,
        created_at=deployment.created_at.isoformat(),
    )

@router.put("/{deployment_id}", response_model=DeploymentResponse)
async def update_deployment_endpoint(
    deployment_id: UUID,
    deployment_update: DeploymentUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
    if not deployment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found")
    for key, value in deployment_update.dict(exclude_unset=True).items():
        setattr(deployment, key, value)
    db.commit()
    db.refresh(deployment)
    return DeploymentResponse(
        id=deployment.id,
        name=deployment.name,
        description=deployment.description,
        backend_image=deployment.backend_image,
        frontend_image=deployment.frontend_image,
        database_image=deployment.database_image,
        created_at=deployment.created_at.isoformat(),
    )

@router.delete("/{deployment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deployment_endpoint(
    deployment_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
    if not deployment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found")
    db.delete(deployment)
    db.commit()
    return None

# Docker Compose setup endpoint
@router.post("/setup", status_code=status.HTTP_200_OK)
async def setup_docker_compose_endpoint(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    deployments = db.query(Deployment).all()
    if not deployments:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No deployments found")

    compose_file_content = {
        "version": "3.8",
        "services": {
            deployment.name: {
                "image": deployment.backend_image,
                "ports": ["8000:8000"],
                "environment": ["DATABASE_URL=postgres://user:password@db:5432/dbname"],
            }
            for deployment in deployments
        },
    }

    # Add database service
    compose_file_content["services"]["db"] = {
        "image": "postgres:latest",
        "ports": ["5432:5432"],
        "environment": ["POSTGRES_USER=user", "POSTGRES_PASSWORD=password", "POSTGRES_DB=dbname"],
    }

    # Add frontend service
    compose_file_content["services"]["frontend"] = {
        "image": "frontend:latest",
        "ports": ["3000:3000"],
    }

    return compose_file_content