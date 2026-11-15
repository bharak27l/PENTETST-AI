from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.routes import router as api_router
from app.core.auth import hash_password
from app.core.config import settings
from app.database import create_user, initialize_database, get_user_by_username


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    if settings.bootstrap_username and settings.bootstrap_password:
        existing = get_user_by_username(settings.bootstrap_username)
        if existing is None:
            create_user(settings.bootstrap_username, hash_password(settings.bootstrap_password))
    yield


app = FastAPI(title=settings.app_name, version=settings.app_version,
              description="PENTETST-AI: safe, modular security testing orchestration and reporting.", lifespan=lifespan)
app.include_router(api_router, prefix="/api")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.state.templates = Jinja2Templates(directory="app/templates")


@app.get("/")
async def index(request):
    return app.state.templates.TemplateResponse("index.html", {"request": request, "title": settings.app_name})


@app.get("/health")
async def healthcheck():
    return {"status": "ok", "app": settings.app_name}
