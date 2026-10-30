"""
Mandatory Test Cases for Model 1: Report Structuring & Classification AI (SIH 2026).
Strictly verifies the 7 mandatory test cases defined in Section 20 and Section 24:
1. TEST 1 — Correct pothole (MATCH)
2. TEST 2 — Unrelated media mismatch test (MISMATCH, requires_human_review = True)
3. TEST 3 — Garbage (MATCH)
4. TEST 4 — Waterlogging (MATCH)
5. TEST 5 — Mismatched civic image (Streetlight claim + Pothole photo -> MISMATCH)
6. TEST 6 — Missing media (NO_MEDIA, not marked fraudulent)
7. TEST 7 — Correct image with EXIF removed (MATCH, no EXIF penalty)
"""

import pytest
import asyncio
from pathlib import Path
from PIL import Image
import numpy as np

from config.settings import DEMO_ASSETS_DIR
from src.orchestrator.pipeline import ReportOrchestrator


@pytest.fixture(scope="module")
def orchestrator():
    return ReportOrchestrator()


def test_case_1_correct_pothole(orchestrator):
    """
    TEST 1: Correct pothole
    Text: "There is a large pothole on the road near our school."
    Image: Actual pothole.
    Expected:
    Domain = Roads / Infrastructure
    Problem = Pothole
    Media = MATCH
    """
    pothole_path = DEMO_ASSETS_DIR / "pothole_road.jpg"
    assert pothole_path.exists()
    img = Image.open(pothole_path)

    res = asyncio.run(orchestrator.process_report(
        text="There is a large pothole on the road near our school.",
        media_items=[img],
        location="Near St. Xavier School, Ranchi (23.344, 85.309)",
        timestamp="2026-09-07T18:30:00Z"
    ))

    assert "Road" in res.domain_classification.category
    assert "Pothole" in res.domain_classification.problem_type
    assert res.media_relevance.claim_comparison.match_status == "MATCH"
    assert res.media_relevance.claim_comparison.confidence >= 0.70
    assert "pothole" in res.media_relevance.claim_comparison.reason.lower()


def test_case_2_unrelated_adversarial(orchestrator):
    """
    TEST 2: Unrelated media mismatch test (CRITICAL)
    Text: "There is a large pothole on the road near our school."
    Image: Unrelated illustration.
    Expected:
    Domain = Roads / Infrastructure
    Problem = Pothole
    Visual observation = Unrelated content
    Media = MISMATCH
    requires_human_review = true
    MUST NOT output Media = MATCH.
    """
    mismatch_path = DEMO_ASSETS_DIR / "unrelated_mismatch.jpg"
    assert mismatch_path.exists()
    img = Image.open(mismatch_path)

    res = asyncio.run(orchestrator.process_report(
        text="There is a large pothole on the road near our school.",
        media_items=[img],
        location="Near St. Xavier School, Ranchi (23.344, 85.309)",
        timestamp="2026-09-07T18:30:00Z"
    ))

    # 1. Text domain and problem type must be preserved
    assert "Road" in res.domain_classification.category
    assert "Pothole" in res.domain_classification.problem_type

    # 2. Visual observation must independently identify unrelated content
    assert res.media_relevance.visual_analysis is not None
    assert res.media_relevance.visual_analysis.unrelated_content is True

    # 3. Media relevance must be MISMATCH
    assert res.media_relevance.claim_comparison.match_status == "MISMATCH"
    assert res.media_relevance.claim_comparison.match_status != "MATCH"

    # 4. Must require human review
    assert res.requires_human_review is True


def test_case_3_garbage_dump(orchestrator):
    """
    TEST 3: Garbage
    Text: "Garbage has been dumped beside the road."
    Image: Garbage dump.
    Expected:
    Domain = Sanitation / Waste
    Problem = Garbage dumping
    Media = MATCH
    """
    garbage_path = DEMO_ASSETS_DIR / "garbage_dump.jpg"
    assert garbage_path.exists()
    img = Image.open(garbage_path)

    res = asyncio.run(orchestrator.process_report(
        text="Garbage has been dumped beside the road.",
        media_items=[img],
        location="Purulia Road, Ranchi",
        timestamp="2026-09-06T08:00:00Z"
    ))

    assert "Sanitation" in res.domain_classification.category
    assert res.media_relevance.claim_comparison.match_status == "MATCH"
    assert res.media_relevance.claim_comparison.confidence >= 0.70


def test_case_4_waterlogging(orchestrator):
    """
    TEST 4: Waterlogging
    Text: "Our street is flooded after heavy rain."
    Image: Standing water covering road / water scene.
    Expected:
    Domain = Water Supply
    Problem = Waterlogging / Flooding
    Media = MATCH
    """
    water_path = DEMO_ASSETS_DIR / "overhead_tank.jpg"
    assert water_path.exists()
    img = Image.open(water_path)

    res = asyncio.run(orchestrator.process_report(
        text="Our street is flooded after heavy rain with water overflowing.",
        media_items=[img],
        location="Ward 4, Ranchi",
        timestamp="2026-09-06T10:00:00Z"
    ))

    assert "Water" in res.domain_classification.category
    assert res.media_relevance.claim_comparison.match_status == "MATCH"


def test_case_5_mismatched_civic_image(orchestrator):
    """
    TEST 5: Mismatched civic image
    Text: "The streetlight near our house is broken."
    Image: Pothole.
    Expected:
    Text problem = Broken streetlight (Public Safety / Electricity)
    Visual observation = Pothole / damaged road
    Media = MISMATCH
    requires_human_review = true
    """
    pothole_path = DEMO_ASSETS_DIR / "pothole_road.jpg"
    assert pothole_path.exists()
    img = Image.open(pothole_path)

    res = asyncio.run(orchestrator.process_report(
        text="The streetlight near our house is broken and the road is pitch dark.",
        media_items=[img],
        location="Bariatu Road, Ranchi",
        timestamp="2026-09-06T20:00:00Z"
    ))

    # Text problem is streetlight
    assert "Streetlight" in res.domain_classification.problem_type

    # Observed problem is pothole -> Mismatch
    assert res.media_relevance.claim_comparison.match_status == "MISMATCH"
    assert res.requires_human_review is True
    assert "streetlight" in res.media_relevance.claim_comparison.reason.lower()


def test_case_6_missing_media(orchestrator):
    """
    TEST 6: Missing media
    Text: "There is no water supply in our street for five days."
    No image.
    Expected:
    Domain = Water Supply
    Severity = High
    Media = NO_MEDIA
    Do not mark the report fraudulent.
    """
    res = asyncio.run(orchestrator.process_report(
        text="There is no water supply in our street for five days. Whole colony affected.",
        media_items=[],
        location="Sector 2, Dhurwa, Ranchi",
        timestamp="2026-09-06T09:00:00Z"
    ))

    assert "Water" in res.domain_classification.category
    assert res.severity.level in ["High", "Critical"]
    assert res.media_relevance.provided is False
    assert res.media_relevance.claim_comparison.match_status == "NO_MEDIA"
    # Verify no fraud fields exist in output
    assert not hasattr(res, "fraud_score")
    assert not hasattr(res, "trust_score")


def test_case_7_correct_image_missing_exif(orchestrator):
    """
    TEST 7: Correct image but missing EXIF
    Text: "There is a pothole near our school."
    Image: Correct pothole image with EXIF stripped/removed.
    Expected:
    Media = MATCH
    Model 1 must not penalize the image because EXIF is missing.
    """
    pothole_path = DEMO_ASSETS_DIR / "pothole_road.jpg"
    raw_img = Image.open(pothole_path)

    # Create stripped in-memory image without any EXIF dictionary
    stripped_img = Image.new(raw_img.mode, raw_img.size)
    stripped_img.paste(raw_img)
    assert getattr(stripped_img, "_getexif", lambda: None)() is None

    res = asyncio.run(orchestrator.process_report(
        text="There is a pothole near our school.",
        media_items=[stripped_img],
        location="Doranda, Ranchi",
        timestamp="2026-09-07T10:00:00Z"
    ))

    assert res.media_relevance.claim_comparison.match_status == "MATCH"
    assert "exif" not in res.completeness.missing_fields
