from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.routes import router as api_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="PENTETST-AI: safe, modular security testing orchestration and reporting.",
)

app.include_router(api_router, prefix="/api")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.state.templates = Jinja2Templates(directory="app/templates")

@app.get("/")
async def index(request):
    return app.state.templates.TemplateResponse(
        "index.html",
        {"request": request, "title": settings.app_name},
    )

@app.get("/health")
async def healthcheck():
    return {"status": "ok", "app": settings.app_name}
