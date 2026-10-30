import pytest
from fastapi.testclient import TestClient
from pathlib import Path

from src.api.app import app
from config.settings import DEMO_ASSETS_DIR


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "models" in data


def test_taxonomy_endpoint(client):
    res = client.get("/taxonomy")
    assert res.status_code == 200
    data = res.json()
    assert "categories" in data
    assert len(data["categories"]) >= 8
    cat_names = [c["name"] for c in data["categories"]]
    assert "Water Supply" in cat_names
    assert "Electricity" in cat_names
    assert any("Road" in n for n in cat_names)


def test_demo_scenarios_endpoint(client):
    res = client.get("/demo-scenarios")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 5
    assert data[0]["id"] == "scenario_1_overhead_tank"
    scenario_ids = [s["id"] for s in data]
    assert "scenario_3_mismatch" in scenario_ids
    assert "scenario_5_low_quality" in scenario_ids


def test_flagship_overhead_tank_multipart_api(client):
    tank_img_path = DEMO_ASSETS_DIR / "overhead_tank.jpg"
    assert tank_img_path.exists()

    with open(tank_img_path, "rb") as f:
        files = [
            ("media", ("overhead_tank.jpg", f.read(), "image/jpeg"))
        ]

    data = {
        "text": "Citizen reports repeated overhead-tank overflow in Ward 4. Clean drinking water flooding the road and entering houses for 3 days.",
        "location": "Ward 4, Near Water Tank, Morabadi, Ranchi (23.3850, 85.3340)",
        "timestamp": "2026-09-06T10:00:00Z",
        "report_id": "TEST-REP-001"
    }

    res = client.post("/classify-report", data=data, files=files)
    assert res.status_code == 200
    payload = res.json()

    # Verify strict schema compliance
    assert payload["report_id"] == "TEST-REP-001"
    assert payload["domain_classification"]["category"] == "Water Supply"
    assert payload["domain_classification"]["confidence"] > 0.60
    assert payload["severity"]["level"] in ["High", "Critical"]
    assert payload["completeness"]["score"] >= 0.85
    assert payload["media_relevance"]["provided"] is True
    assert payload["media_relevance"]["claim_comparison"]["match_status"] == "MATCH"
    assert payload["overall_confidence"] > 0.70
    assert payload["processing_metadata"]["processing_time_ms"] > 0


def test_unrelated_mismatch_multipart_api(client):
    mismatch_path = DEMO_ASSETS_DIR / "unrelated_mismatch.jpg"
    assert mismatch_path.exists()

    with open(mismatch_path, "rb") as f:
        files = [
            ("media", ("unrelated_mismatch.jpg", f.read(), "image/jpeg"))
        ]

    data = {
        "text": "There is a large pothole on the road near our school.",
        "location": "Opposite St. Xavier School Gate, Doranda, Ranchi (23.3440, 85.3090)",
        "timestamp": "2026-09-07T18:30:00Z"
    }

    res = client.post("/classify-report", data=data, files=files)
    assert res.status_code == 200
    payload = res.json()

    assert "Road" in payload["domain_classification"]["category"]
    assert "Pothole" in payload["domain_classification"]["problem_type"]
    assert payload["media_relevance"]["provided"] is True
    assert payload["media_relevance"]["visual_analysis"]["unrelated_content"] is True
    assert payload["media_relevance"]["claim_comparison"]["match_status"] == "MISMATCH"
    assert payload["requires_human_review"] is True


def test_media_mismatch_multipart_api(client):
    selfie_path = DEMO_ASSETS_DIR / "selfie_mismatch.jpg"
    with open(selfie_path, "rb") as f:
        files = [
            ("media", ("selfie_mismatch.jpg", f.read(), "image/jpeg"))
        ]

    data = {
        "text": "Huge 4-feet wide pothole on highway bridge bypass. Multiple two-wheelers slipping and falling daily.",
        "location": "Highway Bypass Bridge, Sector 4, Bokaro (23.6693, 86.1511)",
        "timestamp": "2026-09-06T09:30:00Z"
    }

    res = client.post("/classify-report", data=data, files=files)
    assert res.status_code == 200
    payload = res.json()

    assert "Road" in payload["domain_classification"]["category"]
    assert payload["media_relevance"]["provided"] is True
    assert payload["media_relevance"]["claim_comparison"]["match_status"] == "MISMATCH"
    assert payload["requires_human_review"] is True


def test_real_pothole_multipart_api(client):
    real_path = DEMO_ASSETS_DIR / "real_pothole.jpg"
    with open(real_path, "rb") as f:
        files = [
            ("media", ("real_pothole.jpg", f.read(), "image/jpeg"))
        ]

    data = {
        "text": "Huge 4-feet wide pothole on highway bridge bypass. Multiple two-wheelers slipping and falling daily.",
        "location": "Highway Bypass Bridge, Sector 4, Bokaro (23.6693, 86.1511)",
        "timestamp": "2026-09-06T09:30:00Z"
    }

    res = client.post("/classify-report", data=data, files=files)
    assert res.status_code == 200
    payload = res.json()

    assert "Road" in payload["domain_classification"]["category"]
    assert payload["media_relevance"]["provided"] is True
    assert payload["media_relevance"]["claim_comparison"]["match_status"] == "MATCH"
    assert payload["media_relevance"]["claim_comparison"]["confidence"] >= 0.70


def test_json_endpoint(client):
    payload = {
        "text": "Distribution transformer sparking loudly and catching fire near Main Road market. Danger of blast!",
        "location": "Main Road Market, Ranchi (23.36, 85.32)",
        "timestamp": "2026-09-06T12:00:00Z",
        "demo_asset_name": "sparking_wire.jpg"
    }
    res = client.post("/classify-report-json", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["domain_classification"]["category"] == "Electricity"
    assert data["severity"]["level"] == "Critical"
    assert data["requires_human_review"] is True


def test_model2_contract_endpoint(client):
    payload = {
        "text": "There is a large pothole on the road near our school.",
        "location": "Doranda, Ranchi",
        "timestamp": "2026-09-07T10:00:00Z",
        "demo_asset_name": "pothole_road.jpg"
    }
    res = client.post("/model2-contract", json=payload)
    assert res.status_code == 200
    contract = res.json()
    assert "Road" in contract["reported_domain"]
    assert "Pothole" in contract["reported_problem"]
    assert contract["media_match_status"] == "MATCH"
    assert "media_visual_description" in contract
    assert "media_visual_concepts" in contract
