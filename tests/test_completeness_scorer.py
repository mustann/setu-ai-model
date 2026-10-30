import pytest
from src.completeness_scorer.scorer import CompletenessScorer


@pytest.fixture
def scorer():
    return CompletenessScorer()


def test_flagship_complete_report(scorer):
    # Flagship: detailed text + photo + GPS + valid timestamp
    res = scorer.evaluate(
        text="Citizen reports repeated overhead-tank overflow in Ward 4. Clean drinking water flooding the road and entering houses for 3 days.",
        media_count=1,
        location="Ward 4, Near Water Tank, Morabadi, Ranchi (23.3850, 85.3340)",
        timestamp="2026-09-06T10:00:00Z"
    )
    assert res.score >= 0.85
    assert len(res.missing_fields) == 0
    assert len(res.suggestions_for_citizen) == 0


def test_vague_incomplete_report(scorer):
    # Vague text ("bad road"), no media, vague location, no timestamp
    res = scorer.evaluate(
        text="bad road",
        media_count=0,
        location="my area",
        timestamp=None
    )
    assert res.score <= 0.40
    assert "media_attachment" in res.missing_fields
    assert "detailed_description" in res.missing_fields
    assert "timestamp" in res.missing_fields
    assert "precise_location" in res.missing_fields
    assert len(res.suggestions_for_citizen) >= 3


def test_no_media_only(scorer):
    res = scorer.evaluate(
        text="A very detailed description of a sewage pipe leaking onto the main market street near clock tower.",
        media_count=0,
        location="Clock Tower, Main Market, Ranchi (23.35, 85.33)",
        timestamp="2026-09-05T12:30:00Z"
    )
    # Location(0.35) + Text(0.25) + Timestamp(0.10) = 0.70
    assert 0.65 <= res.score <= 0.75
    assert "media_attachment" in res.missing_fields
