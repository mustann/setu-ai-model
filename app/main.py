"""
FastAPI Main Application Entrypoint for Report Structuring & Classification AI.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.utils.config import settings

app = FastAPI(
    title="Report Structuring & Classification AI",
    description=(
        "Stage 1 Civic Intelligence Pipeline: Transforms unstructured citizen reports "
        "(text, optional media, location, timestamp) into structured, explainable civic records."
    ),
    version=settings.version,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(router)


@app.get("/")
async def root():
    return {
        "message": "Report Structuring & Classification AI API is running.",
        "docs": "/docs",
        "health": "/health"
    }
