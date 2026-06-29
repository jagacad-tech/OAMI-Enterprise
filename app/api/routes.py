"""
OAMI API Routes
"""

from fastapi import APIRouter

from app.core.config import config

router = APIRouter()


@router.get("/")
def home():
    return {
        "application": config.settings.app.name,
        "version": config.settings.app.version,
        "status": "running",
    }


@router.get("/health")
def health():
    return {
        "status": "healthy"
    }