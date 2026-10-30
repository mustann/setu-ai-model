"""
Unified Vision Checker Module for Model 1 (SIH 2026).
Orchestrates:
1. Independent Image Analysis (ImageAnalyzer)
2. Video keyframe sampling & deduplication (VideoProcessor)
3. Text-to-Media semantic claim comparison (MediaComparator)
Strictly adheres to Model 1 boundaries: does NOT evaluate image trust, fraud, or EXIF tampering.
"""

import io
import os
from pathlib import Path
from typing import List, Optional, Union, Tuple
from PIL import Image

from config.settings import load_taxonomy, Taxonomy
from .visual_concepts import load_visual_taxonomy, VisualConceptTaxonomy
from .image_analyzer import ImageAnalyzer, VisualAnalysisResult, VisualConceptItem
from .video_processor import VideoProcessor
from .media_comparator import MediaComparator, MediaRelevanceResult, ClaimComparisonResult


class VisionChecker:
    def __init__(
        self,
        taxonomy: Optional[Taxonomy] = None,
        visual_taxonomy: Optional[VisualConceptTaxonomy] = None
    ):
        self.taxonomy = taxonomy or load_taxonomy()
        self.visual_taxonomy = visual_taxonomy or load_visual_taxonomy()
        self.image_analyzer = ImageAnalyzer(visual_taxonomy=self.visual_taxonomy)
        self.video_processor = VideoProcessor(max_frames=8)
        self.media_comparator = MediaComparator()

    def _aggregate_visual_analyses(
        self,
        analyses: List[VisualAnalysisResult],
        is_video: bool = False
    ) -> VisualAnalysisResult:
        """
        Aggregates observations across multiple image or video frames.
        """
        if not analyses:
            return VisualAnalysisResult(
                visual_description="No visual content could be analyzed.",
                visual_concepts=[],
                unrelated_content=False,
                is_blurry=False,
                top_category="Other",
                top_problem_type="Other"
            )

        if len(analyses) == 1:
            res = analyses[0]
            if is_video:
                res.visual_description = f"[Video Analysis] {res.visual_description}"
            return res

        # Aggregate across frames:
        # Check if majority of frames are unrelated
        unrelated_count = sum(1 for a in analyses if a.unrelated_content)
        is_unrelated = (unrelated_count / len(analyses)) >= 0.5

        # Check blur
        blurry_count = sum(1 for a in analyses if a.is_blurry)
        is_blurry = (blurry_count / len(analyses)) >= 0.75

        # Pool concepts by label with max or average confidence
        concept_scores = {}
        for a in analyses:
            for c in a.visual_concepts:
                if c.label not in concept_scores:
                    concept_scores[c.label] = []
                concept_scores[c.label].append(c.confidence)

        aggregated_concepts = [
            VisualConceptItem(label=lbl, confidence=round(float(sum(scores) / len(scores)), 2))
            for lbl, scores in sorted(concept_scores.items(), key=lambda x: max(x[1]), reverse=True)
        ]

        # Select most common observed problem type / category
        problem_counts = {}
        for a in analyses:
            key = (a.top_category, a.top_problem_type)
            problem_counts[key] = problem_counts.get(key, 0) + 1

        top_key = max(problem_counts.items(), key=lambda x: x[1])[0]
        top_cat, top_prob = top_key

        labels_summary = ", ".join([c.label for c in aggregated_concepts[:2]])
        prefix = f"[Video Analysis across {len(analyses)} useful keyframes] " if is_video else f"[Analysis across {len(analyses)} images] "
        desc = prefix + f"Observed visual elements of {labels_summary} consistent with {top_prob}."

        avg_sharpness = float(sum(a.sharpness_score for a in analyses) / len(analyses))

        return VisualAnalysisResult(
            visual_description=desc,
            visual_concepts=aggregated_concepts[:3],
            unrelated_content=is_unrelated,
            is_blurry=is_blurry,
            sharpness_score=round(avg_sharpness, 2),
            top_category=top_cat,
            top_problem_type=top_prob
        )

    def evaluate_media(
        self,
        media_items: List[Union[Image.Image, str, Path, bytes]],
        domain: str,
        problem_type: Optional[str] = None,
        is_video: bool = False
    ) -> MediaRelevanceResult:
        """
        Evaluates one or more uploaded media files (photos or video)
        independently first, then compares with reported claim.
        """
        reported_problem = problem_type or domain or "Civic Grievance"

        if not media_items:
            return self.media_comparator.compare(
                reported_category=domain,
                reported_problem=reported_problem,
                visual_analysis=None,
                media_type=None,
                frames_checked=0
            )

        frames_to_check: List[Image.Image] = []
        frames_sampled_total = 0

        if is_video:
            for item in media_items:
                if isinstance(item, (str, Path)):
                    frames, sampled = self.video_processor.extract_keyframes_from_path(item)
                    frames_to_check.extend(frames)
                    frames_sampled_total += sampled
                elif isinstance(item, bytes):
                    frames, sampled = self.video_processor.extract_keyframes_from_bytes(item)
                    frames_to_check.extend(frames)
                    frames_sampled_total += sampled
        else:
            for item in media_items:
                if isinstance(item, Image.Image):
                    frames_to_check.append(item)
                    frames_sampled_total += 1
                elif isinstance(item, (str, Path)) and os.path.exists(str(item)):
                    try:
                        img = Image.open(str(item)).convert("RGB")
                        frames_to_check.append(img)
                        frames_sampled_total += 1
                    except Exception:
                        pass
                elif isinstance(item, bytes):
                    try:
                        img = Image.open(io.BytesIO(item)).convert("RGB")
                        frames_to_check.append(img)
                        frames_sampled_total += 1
                    except Exception:
                        pass

        if not frames_to_check:
            # File unreadable or empty
            return MediaRelevanceResult(
                provided=True,
                media_type="video" if is_video else "image",
                visual_analysis=None,
                claim_comparison=ClaimComparisonResult(
                    reported_problem=reported_problem,
                    observed_problem="None",
                    match_status="UNCERTAIN",
                    confidence=0.10,
                    reason="Media file could not be decoded or contained no readable frames."
                ),
                frames_checked=0
            )

        # 1. Independently analyze each useful frame
        frame_analyses: List[VisualAnalysisResult] = [
            self.image_analyzer.analyze_image(frame)
            for frame in frames_to_check
        ]

        # 2. Aggregate observations across frames
        aggregated_analysis = self._aggregate_visual_analyses(frame_analyses, is_video=is_video)

        # 3. Compare independent visual observation against reported claim
        media_type = "video" if is_video else "image"
        frames_checked = frames_sampled_total if is_video else len(frames_to_check)

        return self.media_comparator.compare(
            reported_category=domain,
            reported_problem=reported_problem,
            visual_analysis=aggregated_analysis,
            media_type=media_type,
            frames_checked=frames_checked
        )
