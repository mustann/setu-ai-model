import pytest
from src.severity_scorer.scorer import SeverityScorer


@pytest.fixture
def scorer():
    return SeverityScorer()


def test_flagship_overhead_tank(scorer):
    # Flagship: overhead tank overflow for 3 days entering houses
    text = "Citizen reports repeated overhead-tank overflow in Ward 4. Clean drinking water entering houses for 3 days."
    res = scorer.evaluate(text, domain="Water Supply")
    assert res.level in ["High", "Critical"]
    assert res.confidence >= 0.70
    assert any("houses" in s.lower() or "duration" in s.lower() for s in res.signals)


def test_critical_sparking_wire_near_school(scorer):
    text = "11kV high-tension wire snapped and sparking in front of primary school gate. Children at risk!"
    res = scorer.evaluate(text, domain="Electricity")
    assert res.level == "Critical"
    assert res.confidence >= 0.80
    assert any("hazard" in s.lower() for s in res.signals)
    assert any("children" in s.lower() or "school" in s.lower() for s in res.signals)


def test_low_severity_minor_issue(scorer):
    text = "Minor street light bulb flickering near house 12. Small issue, kindly check whenever possible."
    res = scorer.evaluate(text, domain="Public Safety")
    assert res.level == "Low"
    assert res.confidence >= 0.60


def test_empty_text(scorer):
    res = scorer.evaluate("")
    assert res.level == "Low"
    assert len(res.signals) > 0
