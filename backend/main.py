from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from datetime import datetime
from database.config import init_db
from backend.lifespan import lifespan
from backend.exception_handlers import general_exception_handler, validation_exception_handler, http_exception_handler
from backend.routers.backend import router as backend_router
from backend.routers.auth import router as auth_router
from backend.routers.file_upload import router as file_upload_router
from backend.routers.ingestion_pipeline import router as ingestion_pipeline_router
from backend.routers.query_pipeline import router as query_pipeline_router
from backend.routers.deployment import router as deployment_router
from ai.routes import router as ai_router

# Initialize FastAPI app
app = FastAPI(
    title="Aakaar Project API",
    description="Backend API for the Aakaar Project, supporting AI and web application functionalities.",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
init_db()

# Mount routers
app.include_router(backend_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(file_upload_router, prefix="/api")
app.include_router(ingestion_pipeline_router, prefix="/api")
app.include_router(query_pipeline_router, prefix="/api")
app.include_router(deployment_router, prefix="/api")
app.include_router(ai_router, prefix="/api")

# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return await http_exception_handler(request, exc)

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return await validation_exception_handler(request, exc)

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return await general_exception_handler(request, exc)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
    }