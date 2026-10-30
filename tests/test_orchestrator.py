import pytest
import asyncio
from PIL import Image
from src.orchestrator.pipeline import ReportOrchestrator
from config.settings import DEMO_ASSETS_DIR


@pytest.fixture(scope="module")
def orchestrator():
    return ReportOrchestrator()


def test_flagship_overhead_tank_orchestration(orchestrator):
    tank_img = Image.open(DEMO_ASSETS_DIR / "overhead_tank.jpg")
    output = asyncio.run(orchestrator.process_report(
        text="Citizen reports repeated overhead-tank overflow in Ward 4. Clean drinking water flooding the road and entering houses for 3 days.",
        media_items=[tank_img],
        location="Ward 4, Near Water Tank, Morabadi, Ranchi (23.3850, 85.3340)",
        timestamp="2026-09-06T10:00:00Z"
    ))

    # 1. Domain & Problem Type
    assert "Water" in output.domain_classification.category
    assert output.domain_classification.confidence > 0.60
    assert output.domain_classification.problem_type in ["Tank Overflow", "Flooding", "Waterlogging"]
    assert len(output.domain_classification.reason) > 0

    # 2. Severity
    assert output.severity.level in ["High", "Critical"]
    assert output.severity.confidence > 0.70
    assert len(output.severity.signals) >= 1
    assert len(output.severity.reason) > 0

    # 3. Completeness
    assert output.completeness.score >= 0.85
    assert len(output.completeness.missing_fields) == 0

    # 4. Media Relevance
    assert output.media_relevance.provided is True
    assert output.media_relevance.claim_comparison.match_status == "MATCH"
    assert output.media_relevance.frames_checked == 1

    # 5. Model 2 Integration Contract export
    m2 = output.to_model2_contract()
    assert m2["reported_domain"] == output.domain_classification.category
    assert m2["media_match_status"] == "MATCH"

    # 6. Overall
    assert output.overall_confidence > 0.70
    assert output.processing_metadata.processing_time_ms > 0
    assert output.processing_metadata.offline_mode_used is True


def test_mismatched_media_flagged_for_human_review(orchestrator):
    selfie_img = Image.open(DEMO_ASSETS_DIR / "selfie_mismatch.jpg")
    output = asyncio.run(orchestrator.process_report(
        text="Massive pothole on highway bridge bypass. Motorcyclists slipping and falling daily.",
        media_items=[selfie_img],
        location="Highway Bridge, Ranchi (23.35, 85.32)",
        timestamp="2026-09-06T11:00:00Z"
    ))

    assert "Road" in output.domain_classification.category
    assert output.media_relevance.provided is True
    assert output.media_relevance.claim_comparison.match_status == "MISMATCH"
    assert output.requires_human_review is True


def test_vague_complaint_triggers_human_review(orchestrator):
    output = asyncio.run(orchestrator.process_report(
        text="bad road",
        media_items=[],
        location="my area",
        timestamp=None
    ))

    assert output.completeness.score < 0.50
    assert output.media_relevance.provided is False
    assert "media_attachment" in output.completeness.missing_fields
    assert output.requires_human_review is True
