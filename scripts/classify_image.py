"""
Run the SIH 2026 Multi-Modal Report Structuring & Classification pipeline
on a user-specified image attachment and complaint text.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from PIL import Image
from src.orchestrator.pipeline import ReportOrchestrator
from config.settings import DEMO_ASSETS_DIR



def main():
    parser = argparse.ArgumentParser(description="Classify civic report with image media.")
    parser.add_argument(
        "--image",
        type=str,
        default=str(DEMO_ASSETS_DIR / "real_pothole.jpg"),
        help="Path to image file"
    )
    parser.add_argument(
        "--text",
        type=str,
        default="Huge 4-feet wide pothole on highway bridge bypass. Multiple two-wheelers slipping and falling daily.",
        help="Citizen complaint text"
    )
    parser.add_argument(
        "--location",
        type=str,
        default="Highway Bypass Bridge, Sector 4, Bokaro (23.6693, 86.1511)",
        help="GPS / location string"
    )
    parser.add_argument(
        "--timestamp",
        type=str,
        default="2026-09-06T09:30:00Z",
        help="Timestamp string"
    )
    args = parser.parse_args()

    image_path = Path(args.image)
    if not image_path.exists():
        print(f"Error: Image path '{image_path}' does not exist.")
        return

    print("=" * 80)
    print(f"SIH 2026 AI PIPELINE - PROCESSING SUBMISSION WITH IMAGE")
    print("=" * 80)
    print(f"Image File : {image_path.name} ({image_path.stat().st_size / 1024:.1f} KB)")
    print(f"Text Input : {args.text}")
    print(f"Location   : {args.location}")
    print(f"Timestamp  : {args.timestamp}")
    print("-" * 80)

    img = Image.open(image_path).convert("RGB")
    orchestrator = ReportOrchestrator()

    result = asyncio.run(orchestrator.process_report(
        text=args.text,
        media_items=[img],
        location=args.location,
        timestamp=args.timestamp
    ))

    # Display high-level summary
    d = result.domain_classification
    s = result.severity
    c = result.completeness
    m = result.media_relevance
    meta = result.processing_metadata

    print("\nTRIAGE SUMMARY:")
    print(f"  • Domain Detected        : {d.category} (Confidence: {d.confidence * 100:.1f}%)")
    if d.alternate_categories:
        alts = ", ".join([f"{a.category} ({a.confidence * 100:.1f}%)" for a in d.alternate_categories[:2]])
        print(f"    Alternates Ranked      : {alts}")
    print(f"  • Severity Level         : {s.level} (Confidence: {s.confidence * 100:.1f}%)")
    for sig in s.signals:
        print(f"    - Signal: {sig}")
    print(f"  • Completeness Score     : {c.score * 100:.0f}%")
    if c.missing_fields:
        print(f"    - Missing Fields       : {', '.join(c.missing_fields)}")
    print(f"  • Media Verification     : {'MATCHED' if m.match else 'MISMATCH/FLAGGED'} (Confidence: {m.confidence * 100:.1f}%)")
    print(f"    - Justification        : {m.justification}")
    print(f"  • Requires Human Review  : {'YES (Flagged)' if result.requires_human_review else 'NO (Auto-Triage Approved)'}")
    print(f"  • Overall Confidence     : {result.overall_confidence * 100:.1f}%")
    print(f"  • Processing Latency     : {meta.processing_time_ms:.2f} ms")

    print("\n" + "=" * 80)
    print("STRUCTURED JSON OUTPUT:")
    print("=" * 80)
    print(json.dumps(result.model_dump(), indent=2))


if __name__ == "__main__":
    main()
