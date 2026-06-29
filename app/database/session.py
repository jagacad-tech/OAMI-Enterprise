"""
Database Session
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import config

engine = create_engine(
    config.settings.database.url,
    echo=False,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)