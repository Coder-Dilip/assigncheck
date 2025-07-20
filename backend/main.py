from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path

from app.core.config import settings
from app.api.api_v1.api import api_router
from app.core.database import engine
from app.models import Base

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI-Powered Viva Assessment Platform",
    description="An open-source educational platform for AI-enhanced assessments",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Create media directory if it doesn't exist
media_path = Path(settings.MEDIA_STORAGE_PATH)
media_path.mkdir(exist_ok=True)

# Mount static files for media
app.mount("/media", StaticFiles(directory=settings.MEDIA_STORAGE_PATH), name="media")

@app.get("/")
async def root():
    return {
        "message": "AI-Powered Viva Assessment Platform API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
