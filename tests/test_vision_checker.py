import pytest
from pathlib import Path
from PIL import Image
from src.vision_checker.clip_checker import VisionChecker
from config.settings import DEMO_ASSETS_DIR


@pytest.fixture(scope="module")
def vision_checker():
    return VisionChecker()


def test_flagship_overhead_tank_media(vision_checker):
    tank_img_path = DEMO_ASSETS_DIR / "overhead_tank.jpg"
    assert tank_img_path.exists()
    img = Image.open(tank_img_path)
    res = vision_checker.evaluate_media([img], domain="Water Supply", problem_type="Tank Overflow")
    assert res.provided is True
    assert res.claim_comparison.match_status == "MATCH"
    assert res.claim_comparison.confidence >= 0.70
    assert res.frames_checked == 1


def test_road_pothole_media(vision_checker):
    pothole_path = DEMO_ASSETS_DIR / "pothole_road.jpg"
    img = Image.open(pothole_path)
    res = vision_checker.evaluate_media([img], domain="Roads / Infrastructure", problem_type="Pothole")
    assert res.provided is True
    assert res.claim_comparison.match_status == "MATCH"
    assert res.claim_comparison.confidence >= 0.70
    assert "pothole" in res.claim_comparison.reason.lower() or "road" in res.claim_comparison.reason.lower()


def test_unrelated_adversarial_mismatch(vision_checker):
    mismatch_path = DEMO_ASSETS_DIR / "unrelated_mismatch.jpg"
    assert mismatch_path.exists()
    img = Image.open(mismatch_path)
    res = vision_checker.evaluate_media([img], domain="Roads / Infrastructure", problem_type="Pothole")
    assert res.provided is True
    assert res.visual_analysis is not None
    assert res.visual_analysis.unrelated_content is True
    assert res.claim_comparison.match_status == "MISMATCH"
    assert res.claim_comparison.match_status != "MATCH"


def test_selfie_mismatch(vision_checker):
    selfie_path = DEMO_ASSETS_DIR / "selfie_mismatch.jpg"
    img = Image.open(selfie_path)
    # Citizen complains about road, but uploads selfie
    res = vision_checker.evaluate_media([img], domain="Roads / Infrastructure", problem_type="Pothole")
    assert res.provided is True
    assert res.visual_analysis.unrelated_content is True
    assert res.claim_comparison.match_status == "MISMATCH"


def test_blurry_media(vision_checker):
    blur_path = DEMO_ASSETS_DIR / "blurry_sample.jpg"
    img = Image.open(blur_path)
    res = vision_checker.evaluate_media([img], domain="Water Supply", problem_type="Waterlogging")
    assert res.provided is True
    # Section 11: blurry image returns UNCERTAIN
    assert res.claim_comparison.match_status == "UNCERTAIN"
    assert "blurry" in res.claim_comparison.reason.lower() or "quality" in res.claim_comparison.reason.lower()


def test_no_media_fallback(vision_checker):
    res = vision_checker.evaluate_media([], domain="Sanitation / Waste", problem_type="Garbage Dumping")
    assert res.provided is False
    assert res.claim_comparison.match_status == "NO_MEDIA"
    assert res.claim_comparison.confidence == 0.0
    assert "no image" in res.claim_comparison.reason.lower() or "no media" in res.claim_comparison.reason.lower()


def test_video_media_evaluation(vision_checker):
    video_path = DEMO_ASSETS_DIR / "test_video.mp4"
    res = vision_checker.evaluate_media([str(video_path)], domain="Roads / Infrastructure", problem_type="Damaged Road", is_video=True)
    assert res.provided is True
    assert res.frames_checked >= 1
    assert "Video Analysis" in res.visual_analysis.visual_description


def test_real_pothole_image(vision_checker):
    real_path = DEMO_ASSETS_DIR / "real_pothole.jpg"
    assert real_path.exists()
    img = Image.open(real_path)
    res = vision_checker.evaluate_media([img], domain="Roads / Infrastructure", problem_type="Pothole")
    assert res.provided is True
    assert res.claim_comparison.match_status == "MATCH"
    assert res.claim_comparison.confidence >= 0.70
