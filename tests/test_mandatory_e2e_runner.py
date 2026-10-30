import httpx
import json

client = httpx.Client(base_url="http://127.0.0.1:8080", timeout=60.0)

# Check Demo Scenarios endpoint count
scenarios = client.get("/demo-scenarios").json()
print(f"=== DEMO SCENARIOS COUNT: {len(scenarios)} ===")
for sc in scenarios:
    print(f"  - [{sc['id']}] {sc['title']}: {sc['badge']}")
assert len(scenarios) == 5, f"Expected exactly 5 demo scenarios, got {len(scenarios)}"

print("\n=== MANDATORY 5 END-TO-END TESTS ===")

# TEST 1: Water complaint + relevant water image
with open("data/demo_assets/overhead_tank.jpg", "rb") as f:
    r1 = client.post(
        "/classify-report",
        data={
            "text": "Repeated overhead tank overflow is wasting water in our neighborhood.",
            "location": "Ward 4, Ranchi",
            "timestamp": "2026-09-06T10:00:00Z"
        },
        files={"media": ("overhead_tank.jpg", f.read(), "image/jpeg")}
    ).json()

print("TEST 1 (Water + Water Image):")
print(f"  Domain: {r1['domain_classification']['category']}")
print(f"  Problem: {r1['domain_classification']['problem_type']}")
print(f"  Status: {r1['media_relevance']['claim_comparison']['match_status']}")
print(f"  Visual Desc: {r1['media_relevance']['visual_analysis']['visual_description']}")
assert r1["media_relevance"]["claim_comparison"]["match_status"] == "MATCH"

# TEST 2: Pothole complaint + pothole image
with open("data/demo_assets/pothole_road.jpg", "rb") as f:
    r2 = client.post(
        "/classify-report",
        data={
            "text": "There is a large pothole on the road near the school.",
            "location": "Doranda, Ranchi",
            "timestamp": "2026-09-07T08:30:00Z"
        },
        files={"media": ("pothole_road.jpg", f.read(), "image/jpeg")}
    ).json()

print("\nTEST 2 (Pothole + Pothole Image):")
print(f"  Domain: {r2['domain_classification']['category']}")
print(f"  Problem: {r2['domain_classification']['problem_type']}")
print(f"  Status: {r2['media_relevance']['claim_comparison']['match_status']}")
print(f"  Visual Desc: {r2['media_relevance']['visual_analysis']['visual_description']}")
assert r2["media_relevance"]["claim_comparison"]["match_status"] == "MATCH"

# TEST 3: Streetlight complaint + pothole image
with open("data/demo_assets/pothole_road.jpg", "rb") as f:
    r3 = client.post(
        "/classify-report",
        data={
            "text": "The streetlight near my house is broken and not working.",
            "location": "Bariatu Road, Ranchi",
            "timestamp": "2026-09-06T20:00:00Z"
        },
        files={"media": ("pothole_road.jpg", f.read(), "image/jpeg")}
    ).json()

print("\nTEST 3 (Streetlight + Pothole Image Mismatch):")
print(f"  Domain: {r3['domain_classification']['category']}")
print(f"  Problem: {r3['domain_classification']['problem_type']}")
print(f"  Observed: {r3['media_relevance']['claim_comparison']['observed_problem']}")
print(f"  Status: {r3['media_relevance']['claim_comparison']['match_status']}")
print(f"  Requires Human Review: {r3['requires_human_review']}")
assert r3["media_relevance"]["claim_comparison"]["match_status"] == "MISMATCH"
assert r3["requires_human_review"] is True

# TEST 4: Garbage complaint + garbage image
with open("data/demo_assets/garbage_dump.jpg", "rb") as f:
    r4 = client.post(
        "/classify-report",
        data={
            "text": "Garbage has been dumped beside the road and has not been collected for several days.",
            "location": "Purulia Road, Ranchi",
            "timestamp": "2026-09-06T08:00:00Z"
        },
        files={"media": ("garbage_dump.jpg", f.read(), "image/jpeg")}
    ).json()

print("\nTEST 4 (Garbage + Garbage Image):")
print(f"  Domain: {r4['domain_classification']['category']}")
print(f"  Problem: {r4['domain_classification']['problem_type']}")
print(f"  Status: {r4['media_relevance']['claim_comparison']['match_status']}")
print(f"  Visual Desc: {r4['media_relevance']['visual_analysis']['visual_description']}")
assert r4["media_relevance"]["claim_comparison"]["match_status"] == "MATCH"

# TEST 5: Road complaint + blurry civic image
with open("data/demo_assets/blurry_sample.jpg", "rb") as f:
    r5 = client.post(
        "/classify-report",
        data={
            "text": "There is road damage near our street.",
            "location": "Harmu Bypass, Ranchi",
            "timestamp": "2026-09-06T14:00:00Z"
        },
        files={"media": ("blurry_sample.jpg", f.read(), "image/jpeg")}
    ).json()

print("\nTEST 5 (Road Damage + Blurry Image):")
print(f"  Domain: {r5['domain_classification']['category']}")
print(f"  Problem: {r5['domain_classification']['problem_type']}")
print(f"  Status: {r5['media_relevance']['claim_comparison']['match_status']}")
print(f"  Reason: {r5['media_relevance']['claim_comparison']['reason']}")
print(f"  Requires Human Review: {r5['requires_human_review']}")
assert r5["media_relevance"]["claim_comparison"]["match_status"] == "UNCERTAIN"
assert r5["requires_human_review"] is True

# Dynamic Text Change Test
r6 = client.post(
    "/classify-report-json",
    json={"text": "There has been no electricity in our street for three days."}
).json()
print("\nDYNAMIC TEXT TEST (Electricity Outage):")
print(f"  Domain: {r6['domain_classification']['category']}")
print(f"  Problem: {r6['domain_classification']['problem_type']}")
assert r6["domain_classification"]["category"] == "Electricity"
assert "Outage" in r6["domain_classification"]["problem_type"] or "Blackout" in r6["domain_classification"]["problem_type"]

# Dynamic Completeness Test (Short text, no location, no media vs Full report)
r_short = client.post("/classify-report-json", json={"text": "Bad road"}).json()
print(f"\nCOMPLETENESS (Short 'Bad road', no loc, no media): {r_short['completeness']['score']*100}% | Missing: {r_short['completeness']['missing_fields']}")
assert r_short["completeness"]["score"] < 0.40

print("\n>>> ALL 5 MANDATORY TESTS AND DYNAMIC CHECKS PASSED PERFECTLY! <<<")
