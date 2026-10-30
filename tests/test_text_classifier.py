import pytest
from src.text_classifier.classifier import TextClassifier


@pytest.fixture(scope="module")
def classifier():
    return TextClassifier()


def test_flagship_overhead_tank(classifier):
    text = "Citizen reports repeated overhead-tank overflow in Ward 4. Clean drinking water wasting for 3 days."
    res = classifier.classify(text)
    assert res.category == "Water Supply"
    assert res.confidence > 0.60
    assert res.problem_type in ["Tank Overflow", "Flooding", "Waterlogging"]
    assert len(res.reason) > 0


def test_electricity_sparking(classifier):
    text = "High-tension wire snapped and sparking on the road near primary school! Live transformer danger."
    res = classifier.classify(text)
    assert res.category == "Electricity"
    assert res.confidence > 0.65
    assert len(res.problem_type) > 0


def test_road_pothole(classifier):
    text = "Huge crater pothole on station road. Motorcyclists falling down."
    res = classifier.classify(text)
    assert "Road" in res.category
    assert res.problem_type == "Pothole"
    assert "pothole" in res.reason.lower()


def test_sanitation_garbage(classifier):
    text = "Municipal garbage dump overflowing with foul smell and open kooda on roadside."
    res = classifier.classify(text)
    assert "Sanitation" in res.category
    assert "Garbage" in res.problem_type


def test_hinglish_water(classifier):
    text = "Paani ki pipeline phat gayi hai, sadak par saara jal beh raha hai."
    res = classifier.classify(text)
    assert res.category == "Water Supply"


def test_empty_text(classifier):
    res = classifier.classify("")
    assert res.category in ["Other", "Roads / Infrastructure"]
    assert res.confidence <= 0.50
