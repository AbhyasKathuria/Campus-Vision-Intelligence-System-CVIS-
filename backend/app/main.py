import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.core.database import init_db
from app.api.v1.router import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    await init_db()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Campus Vision Intelligence System — Event Photo Finder & Compliance Monitoring",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve stored media files (crops, photos, thumbnails)
os.makedirs(settings.STORAGE_LOCAL_ROOT, exist_ok=True)
app.mount("/media", StaticFiles(directory=settings.STORAGE_LOCAL_ROOT), name="media")

# Mount API Routers
app.include_router(api_router)

@app.get("/")
async def root():
    return {
        "system": settings.PROJECT_NAME,
        "status": "operational",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}
