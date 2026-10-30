"""
FastAPI Routes for Report Structuring & Classification AI (Model 1 - SIH 2026).
"""

import io
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, File, Form, UploadFile, Request, HTTPException, status
from pydantic import BaseModel
from PIL import Image

from config.settings import settings, load_taxonomy, DEMO_ASSETS_DIR
from src.vision_checker.visual_concepts import load_visual_taxonomy
from src.orchestrator.pipeline import ReportOrchestrator
from src.orchestrator.schemas import StructuredReportOutput
from src.models import Model2HandoffContract

router = APIRouter()
orchestrator = ReportOrchestrator()

# Pre-built flagship demonstration scenarios (Strictly 5 scenarios per Section 13)
DEMO_SCENARIOS = [
    {
        "id": "scenario_1_overhead_tank",
        "title": "Flagship: Overhead Tank Overflow",
        "badge": "Water Supply • Match",
        "description": "Repeated overhead tank overflow is wasting water in our neighborhood.",
        "category_expected": "Water Supply",
        "problem_expected": "Tank overflow / water wastage",
        "text": "Repeated overhead tank overflow is wasting water in our neighborhood.",
        "location": "Ward 4, Near Water Tank, Morabadi, Ranchi (23.3850, 85.3340)",
        "timestamp": "2026-09-06T10:00:00Z",
        "media_file": "overhead_tank.jpg",
        "expected_outcome": "Domain: Water Supply, Problem: Tank overflow / water wastage, Media: MATCH, Completeness: High"
    },
    {
        "id": "scenario_2_pothole",
        "title": "Road Damage: Pothole",
        "badge": "Roads / Infrastructure • Match",
        "description": "Large pothole on the road near school with verified image.",
        "category_expected": "Roads / Infrastructure",
        "problem_expected": "Pothole",
        "text": "There is a large pothole on the road near the school.",
        "location": "Near St. Xavier School Gate, Doranda, Ranchi (23.3440, 85.3090)",
        "timestamp": "2026-09-07T08:30:00Z",
        "media_file": "pothole_road.jpg",
        "expected_outcome": "Domain: Roads / Infrastructure, Problem: Pothole, Media: MATCH"
    },
    {
        "id": "scenario_3_mismatch",
        "title": "Media Mismatch Test",
        "badge": "Electricity • Mismatch",
        "description": "Citizen reports broken streetlight, but photograph depicts a road pothole.",
        "category_expected": "Electricity",
        "problem_expected": "Broken streetlight",
        "text": "The streetlight near my house is broken and not working.",
        "location": "Bariatu Road, Near RIMS, Ranchi (23.3890, 85.3520)",
        "timestamp": "2026-09-06T20:00:00Z",
        "media_file": "pothole_road.jpg",
        "expected_outcome": "Domain: Electricity, Problem: Broken streetlight, Observed media: Road damage / pothole, Media: MISMATCH, requires_human_review: true"
    },
    {
        "id": "scenario_4_garbage",
        "title": "Sanitation: Garbage Dump",
        "badge": "Sanitation / Waste • Match",
        "description": "Garbage has been dumped beside the road and has not been collected for several days.",
        "category_expected": "Sanitation / Waste",
        "problem_expected": "Garbage dumping",
        "text": "Garbage has been dumped beside the road and has not been collected for several days.",
        "location": "Opposite Sadar Hospital, Purulia Road, Ranchi (23.3700, 85.3300)",
        "timestamp": "2026-09-06T08:00:00Z",
        "media_file": "garbage_dump.jpg",
        "expected_outcome": "Domain: Sanitation / Waste, Problem: Garbage dumping, Media: MATCH"
    },
    {
        "id": "scenario_5_low_quality",
        "title": "Quality Check: Low-Quality Media",
        "badge": "Roads / Infrastructure • Uncertain",
        "description": "Camera blur prevents confident visual interpretation.",
        "category_expected": "Roads / Infrastructure",
        "problem_expected": "Road damage",
        "text": "There is road damage near our street.",
        "location": "Harmu Bypass Road, Ranchi (23.3560, 85.3120)",
        "timestamp": "2026-09-06T14:00:00Z",
        "media_file": "blurry_sample.jpg",
        "expected_outcome": "Media: UNCERTAIN, Reason: The image may contain relevant road damage, but image quality prevents confident visual interpretation."
    }
]


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "module": "Model 1: Report Structuring & Classification AI",
        "version": settings.version,
        "offline_mode": settings.offline_mode,
        "models": {
            "text_classifier": "TFIDF-LogisticCalibrated-v1.1",
            "vision_checker": "CLIP-ViT-B32-ZeroShot-v1.1",
            "severity_scorer": "SignalRegex-Hybrid-v1.1",
            "completeness_scorer": "WeightedRule-v1.1"
        }
    }


@router.get("/taxonomy")
async def get_taxonomy():
    tax = load_taxonomy()
    return {
        "version": tax.version,
        "default_category": tax.default_category,
        "categories": [
            {
                "id": c.id,
                "name": c.name,
                "aliases": c.aliases,
                "description": c.description,
                "problem_types": [pt.model_dump() for pt in c.problem_types]
            }
            for c in tax.categories
        ]
    }


@router.get("/visual-concepts")
async def get_visual_concepts():
    vt = load_visual_taxonomy()
    return {
        "version": vt.version,
        "civic_concepts": [c.model_dump() for c in vt.get_civic_concepts()],
        "unrelated_concepts": [c.model_dump() for c in vt.get_unrelated_concepts()]
    }


@router.get("/demo-scenarios")
async def get_demo_scenarios():
    return DEMO_SCENARIOS


@router.post("/classify-report", response_model=StructuredReportOutput)
async def classify_report(
    text: str = Form(...),
    location: Optional[str] = Form(None),
    timestamp: Optional[str] = Form(None),
    report_id: Optional[str] = Form(None),
    offline_mode: Optional[bool] = Form(None),
    media: List[UploadFile] = File(default=[])
):
    """
    Main endpoint: Accepts multipart form data (text, media files, location, timestamp).
    Returns strict structured report JSON with domain, problem type, severity, completeness,
    independent visual observation, and text <-> media relevance.
    """
    media_items = []
    is_video = False

    for upload in media:
        if not upload.filename:
            continue
        content = await upload.read()
        file_size = len(content)
        if file_size == 0:
            continue

        mime_type = upload.content_type or "application/octet-stream"
        print(f"[PIPELINE LOG] file received: {upload.filename} | MIME: {mime_type} | file size: {file_size} bytes", flush=True)

        filename_lower = upload.filename.lower()
        if filename_lower.endswith((".mp4", ".mov", ".avi", ".mkv", ".webm")):
            media_items.append(content)
            is_video = True
        else:
            try:
                img = Image.open(io.BytesIO(content)).convert("RGB")
                media_items.append(img)
            except Exception as e:
                print(f"[PIPELINE LOG] Warning decoding {upload.filename}: {e}", flush=True)
                media_items.append(content)

    print(f"[PIPELINE LOG] vision processing started for {len(media_items)} media item(s)", flush=True)
    t_start = time.perf_counter()
    report = await orchestrator.process_report(
        text=text,
        media_items=media_items,
        location=location,
        timestamp=timestamp,
        report_id=report_id,
        is_video=is_video,
        offline_mode=offline_mode
    )
    t_ms = (time.perf_counter() - t_start) * 1000
    print(f"[PIPELINE LOG] vision processing completed in {t_ms:.1f}ms", flush=True)

    if report.media_relevance.visual_analysis:
        concepts = [f"{c.label} ({c.confidence:.2f})" for c in report.media_relevance.visual_analysis.visual_concepts]
        print(f"[PIPELINE LOG] visual concepts returned: {', '.join(concepts)}", flush=True)
    comp = report.media_relevance.claim_comparison
    print(f"[PIPELINE LOG] comparison completed: reported='{comp.reported_problem}', observed='{comp.observed_problem}', status={comp.match_status}, confidence={comp.confidence:.2f}", flush=True)

    return report


class JsonReportRequest(BaseModel):
    text: str
    location: Optional[str] = None
    timestamp: Optional[str] = None
    report_id: Optional[str] = None
    demo_asset_name: Optional[str] = None
    offline_mode: Optional[bool] = None


@router.post("/classify-report-json", response_model=StructuredReportOutput)
async def classify_report_json(payload: JsonReportRequest):
    """
    Convenience JSON endpoint for programmatic testing & scenario execution.
    """
    media_items = []
    is_video = False
    if payload.demo_asset_name:
        asset_path = DEMO_ASSETS_DIR / payload.demo_asset_name
        if asset_path.exists():
            file_size = asset_path.stat().st_size
            mime_type = "video/mp4" if asset_path.suffix.lower() in [".mp4", ".mov", ".avi", ".mkv", ".webm"] else "image/jpeg"
            print(f"[PIPELINE LOG] file received: {payload.demo_asset_name} | MIME: {mime_type} | file size: {file_size} bytes", flush=True)
            if asset_path.suffix.lower() in [".mp4", ".mov", ".avi", ".mkv", ".webm"]:
                media_items.append(str(asset_path))
                is_video = True
            else:
                try:
                    img = Image.open(asset_path).convert("RGB")
                    media_items.append(img)
                except Exception:
                    pass

    print(f"[PIPELINE LOG] vision processing started for {len(media_items)} media item(s)", flush=True)
    t_start = time.perf_counter()
    report = await orchestrator.process_report(
        text=payload.text,
        media_items=media_items,
        location=payload.location,
        timestamp=payload.timestamp,
        report_id=payload.report_id,
        is_video=is_video,
        offline_mode=payload.offline_mode
    )
    t_ms = (time.perf_counter() - t_start) * 1000
    print(f"[PIPELINE LOG] vision processing completed in {t_ms:.1f}ms", flush=True)

    if report.media_relevance.visual_analysis:
        concepts = [f"{c.label} ({c.confidence:.2f})" for c in report.media_relevance.visual_analysis.visual_concepts]
        print(f"[PIPELINE LOG] visual concepts returned: {', '.join(concepts)}", flush=True)
    comp = report.media_relevance.claim_comparison
    print(f"[PIPELINE LOG] comparison completed: reported='{comp.reported_problem}', observed='{comp.observed_problem}', status={comp.match_status}, confidence={comp.confidence:.2f}", flush=True)

    return report


@router.post("/model2-contract", response_model=Model2HandoffContract)
async def get_model2_contract(payload: JsonReportRequest):
    """
    Section 21: Model 2 Integration Contract endpoint.
    Exposes Model 1 structured understanding for downstream Evidence Trust ingestion.
    """
    report = await classify_report_json(payload)
    return Model2HandoffContract(**report.to_model2_contract())
