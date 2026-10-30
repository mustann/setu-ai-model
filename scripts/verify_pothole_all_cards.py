"""
Verify that uploading a pothole image returns one combined JSON response
that populates all four Model 1 UI cards completely.
"""

import httpx
import json

client = httpx.Client(base_url="http://127.0.0.1:8080", timeout=60.0)

with open("data/demo_assets/pothole_road.jpg", "rb") as f:
    files = {"media": ("pothole_road.jpg", f.read(), "image/jpeg")}
    data = {
        "text": "There is a large pothole on the road near our school.",
        "location": "Near St. Xavier School Gate, Doranda, Ranchi (23.3440, 85.3090)",
        "timestamp": "2026-09-07T08:30:00Z"
    }
    r = client.post("/classify-report", data=data, files=files)

assert r.status_code == 200, f"Error: HTTP {r.status_code}: {r.text}"
payload = r.json()

print("=" * 70)
print("  MODEL 1 COMBINED EXECUTION RESULT (ONE RUN POPULATES ALL 4 CARDS)")
print("=" * 70)

# Card 1: Report Understanding
card1 = payload["domain_classification"]
sev = payload["severity"]
print("\n[CARD 1: REPORT UNDERSTANDING]")
print(f"  • Category Domain : {card1['category']}")
print(f"  • Specific Problem: {card1['problem_type']}")
print(f"  • Domain Conf.    : {card1['confidence']*100:.0f}%")
print(f"  • Text Reason     : {card1['reason']}")
print(f"  • Severity Level  : {sev['level']}")
print(f"  • Severity Conf.  : {sev['confidence']*100:.0f}%")
print(f"  • Severity Signals: {sev['signals']}")
assert card1["category"] is not None and card1["category"] != "--"
assert card1["problem_type"] is not None and card1["problem_type"] != "--"
assert sev["level"] is not None

# Card 2: Media Understanding
card2 = payload["media_relevance"]["visual_analysis"]
print("\n[CARD 2: MEDIA UNDERSTANDING]")
print(f"  • What image shows: \"{card2['visual_description']}\"")
concepts_str = [f"{c['label']} ({c['confidence']*100:.0f}%)" for c in card2['visual_concepts']]
print(f"  • Visual Concepts : {concepts_str}")
print(f"  • Unrelated Flag  : {card2['unrelated_content']}")
assert card2["visual_description"] is not None and card2["visual_description"] != "No media inspected yet."
assert len(card2["visual_concepts"]) > 0

# Card 3: Text ↔ Media Check
card3 = payload["media_relevance"]["claim_comparison"]
print("\n[CARD 3: TEXT <-> MEDIA CHECK]")
print(f"  • Reported Problem: {card3['reported_problem']}")
print(f"  • Observed in Media: {card3['observed_problem']}")
print(f"  • Match Status    : {card3['match_status']}")
print(f"  • Match Conf.     : {card3['confidence']*100:.0f}%")
print(f"  • Justification   : \"{card3['reason']}\"")
assert card3["match_status"] == "MATCH"
assert card3["reason"] != "Media comparison pending..."

# Card 4: Completeness & Guidance
card4 = payload["completeness"]
print("\n[CARD 4: COMPLETENESS & GUIDANCE]")
print(f"  • Completeness Score: {card4['score']*100:.0f}%")
print(f"  • Missing Fields    : {card4['missing_fields']}")
print(f"  • Citizen Guidance  : {card4['suggestions_for_citizen']}")
assert card4["score"] > 0

# Top KPIs and Flags
print("\n[TOP SUMMARY & ADVISORY STATUS]")
print(f"  • Overall Confidence   : {payload['overall_confidence']*100:.0f}%")
print(f"  • Requires Human Review: {payload['requires_human_review']}")
print(f"  • Processing Latency   : {payload['processing_metadata']['processing_time_ms']} ms")

print("\n" + "=" * 70)
print("  >>> SUCCESS: ALL 4 CARDS RETURNED FULL DATA IN ONE EXECUTION! <<<")
print("=" * 70)
