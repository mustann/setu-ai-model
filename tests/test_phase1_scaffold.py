"""
Phase 1 verification tests:
Verifies folder structure, configuration, Pydantic schemas, and FastAPI endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.utils.config import settings, load_taxonomy
from app.schemas.report_schema import StructuredReportOutput

client = TestClient(app)


def test_root_endpoint():
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert "Report Structuring & Classification AI" in data["message"]


def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "offline_mode" in data


def test_taxonomy_endpoint():
    res = client.get("/taxonomy")
    assert res.status_code == 200
    data = res.json()
    assert "categories" in data
    categories = data["categories"]
    assert len(categories) >= 8
    # Verify core categories from Section 3
    assert any("Water" in c for c in categories)
    assert any("Electricity" in c for c in categories)
    assert any("Road" in c for c in categories)
    assert any("Sanitation" in c for c in categories)
    assert any("Other" in c for c in categories)


def test_classify_report_multipart_text_only():
    form_data = {
        "text": "There is a large pothole on the road near our school."
    }
    res = client.post("/classify-report", data=form_data)
    assert res.status_code == 200
    data = res.json()

    # Validate strict conformance with Section 5 schema
    parsed = StructuredReportOutput(**data)
    assert parsed.report_id.startswith("REP-")
    assert parsed.media_relevance.provided is False
    assert parsed.media_relevance.match is None
    assert parsed.media_relevance.frames_checked == 0
    assert parsed.requires_human_review is True
    assert "processing_time_ms" in parsed.processing_metadata.model_dump()


def test_classify_report_multipart_with_media_and_coords():
    form_data = {
        "text": "Water pipeline burst flooding the road.",
        "latitude": 23.3440,
        "longitude": 85.3090,
        "address": "Doranda, Ranchi",
        "timestamp": "2026-09-07T12:00:00Z"
    }
    files = {
        "media": ("test_pipe.jpg", b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00", "image/jpeg")
    }
    res = client.post("/classify-report", data=form_data, files=files)
    assert res.status_code == 200
    data = res.json()

    parsed = StructuredReportOutput(**data)
    assert parsed.media_relevance.provided is True
    assert parsed.media_relevance.frames_checked == 1
