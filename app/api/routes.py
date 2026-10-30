"""
FastAPI Route handlers for Report Structuring & Classification AI.
"""

import time
import uuid
from typing import Optional, List
from fastapi import APIRouter, File, Form, UploadFile, HTTPException, status
from app.utils.config import settings, load_taxonomy
from app.utils.logging import logger
from app.schemas.report_schema import (
    StructuredReportOutput,
    DomainClassification,
    AlternateCategory,
    SeverityResult,
    CompletenessResult,
    MediaRelevanceResult,
    ProcessingMetadata,
    ReportInputRequest
)

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint confirming API status and active configuration."""
    return {
        "status": "healthy",
        "module": "Report Structuring & Classification AI (Stage 1)",
        "version": settings.version,
        "offline_mode": settings.offline_mode,
        "environment": settings.environment
    }


@router.get("/taxonomy")
async def get_taxonomy():
    """Returns dynamically loaded civic taxonomy categories."""
    tax = load_taxonomy()
    return {
        "version": tax.version,
        "default_category": tax.default_category,
        "categories": [c.name for c in tax.categories]
    }


@router.post("/classify-report", response_model=StructuredReportOutput)
async def classify_report(
    text: str = Form(..., description="Citizen complaint text description"),
    media: Optional[UploadFile] = File(None, description="Optional photo or video evidence file"),
    latitude: Optional[float] = Form(None, description="Incident latitude coordinate"),
    longitude: Optional[float] = Form(None, description="Incident longitude coordinate"),
    address: Optional[str] = Form(None, description="Location text or address"),
    timestamp: Optional[str] = Form(None, description="ISO-8601 observation timestamp")
):
    """
    Main ingestion endpoint accepting multipart form data.
    Produces strict Section 5 StructuredReportOutput JSON.
    """
    t0 = time.perf_counter()
    report_id = f"REP-{uuid.uuid4().hex[:6].upper()}"

    logger.info(f"Report received [{report_id}]: text='{text[:50]}...', media={media.filename if media else None}")

    # Phase 1 verification stub adhering strictly to Section 5 schema
    has_media = media is not None and bool(media.filename)
    frames_checked = 1 if has_media else 0

    elapsed_ms = int((time.perf_counter() - t0) * 1000)

    return StructuredReportOutput(
        report_id=report_id,
        domain_classification=DomainClassification(
            category="Other",
            confidence=0.50,
            alternate_categories=[],
            justification="Phase 1 initial application scaffold."
        ),
        severity=SeverityResult(
            level="Medium",
            confidence=0.50,
            signals=["Initial phase baseline"],
            justification="Phase 1 initial application scaffold."
        ),
        completeness=CompletenessResult(
            score=0.50,
            missing_fields=[],
            suggestions_for_citizen=[],
            justification="Phase 1 initial application scaffold."
        ),
        media_relevance=MediaRelevanceResult(
            provided=has_media,
            match=None if not has_media else True,
            confidence=0.0 if not has_media else 0.50,
            justification="No media provided." if not has_media else "Media file received for processing.",
            frames_checked=frames_checked
        ),
        requires_human_review=True,
        overall_confidence=0.50,
        processing_metadata=ProcessingMetadata(
            model_versions={"pipeline": "phase1-scaffold-v1.0"},
            processing_time_ms=elapsed_ms,
            offline_mode_used=settings.offline_mode
        )
    )
