"""
FastAPI Service for Report Structuring & Classification AI (SIH 2026).
"""

from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings, DEMO_ASSETS_DIR, BASE_DIR
from src.api.routes import router

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Module 1: Report Structuring & Classification AI for Civic Problem Intelligence Platform (SIH 2026)"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount router
app.include_router(router)

# Mount static files (UI and demo assets)
UI_DIR = BASE_DIR / "ui"
UI_DIR.mkdir(parents=True, exist_ok=True)
DEMO_ASSETS_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/assets", StaticFiles(directory=str(DEMO_ASSETS_DIR)), name="assets")
if UI_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(UI_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    index_file = UI_DIR / "index.html"
    if index_file.exists():
        with open(index_file, "r", encoding="utf-8") as f:
            return f.read()
    return HTMLResponse("<h1>SIH 2026 Civic AI Service Running. UI under initialization...</h1>")


@app.get("/download-zip")
async def download_deployment_zip():
    zip_path = BASE_DIR / "sih2026_model_deployable.zip"
    if not zip_path.exists():
        raise HTTPException(status_code=404, detail="Deployment zip package not found.")
    return FileResponse(
        path=str(zip_path),
        filename="sih2026_model_deployable.zip",
        media_type="application/zip"
    )

