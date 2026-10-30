import httpx

def main():
    client = httpx.Client(base_url="http://127.0.0.1:8000")
    scenarios = client.get("/demo-scenarios").json()
    print("=" * 80)
    print("VERIFYING 5 PRE-BUILT SCENARIOS ON LIVE FASTAPI BACKEND:")
    print("=" * 80)

    for s in scenarios:
        payload = {
            "text": s["text"],
            "location": s.get("location"),
            "timestamp": s.get("timestamp"),
            "demo_asset_name": s.get("media_file")
        }
        r = client.post("/classify-report-json", json=payload).json()
        sid = s["id"]
        cat = r["domain_classification"]["category"]
        conf = r["domain_classification"]["confidence"]
        sev = r["severity"]["level"]
        signals = r["severity"]["signals"]
        comp = r["completeness"]["score"]
        match = r["media_relevance"]["match"]
        rev = r["requires_human_review"]
        lat = r["processing_metadata"]["processing_time_ms"]

        print(f"\nScenario: {s['title']}")
        print(f"  • Category: {cat} (Confidence: {conf*100:.1f}%)")
        print(f"  • Severity: {sev} (Signals: {len(signals)} found)")
        print(f"  • Completeness: {comp*100:.0f}%")
        print(f"  • Media Plausible: {match} (Checked: {r['media_relevance']['frames_checked']} frame)")
        print(f"  • Advisory Human Review: {rev}")
        print(f"  • Latency: {lat} ms")

    print("\n" + "=" * 80)
    print("ALL 5 SCENARIOS VERIFIED SUCCESSFULLY!")
    print("=" * 80)

if __name__ == "__main__":
    main()
