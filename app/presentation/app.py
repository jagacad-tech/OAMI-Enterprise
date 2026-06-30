from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router

app = FastAPI(
    title="OAMI Enterprise",
    version="0.1.0 Alpha",
)

app.include_router(router)

app.mount("/static", StaticFiles(directory="static"), name="static")