"""
FastAPI Application
"""

from fastapi import FastAPI

from app.api.routes import router
from app.core.config import config

app = FastAPI(
    title=config.settings.app.name,
    version=config.settings.app.version,
)

app.include_router(router)