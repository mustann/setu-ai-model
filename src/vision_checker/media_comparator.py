"""
Media Comparator Module for Model 1.
Performs semantic text <-> image claim comparison:
Compares what the citizen claims against what the image visibly shows.
Outputs strict claim_comparison adhering to Section 9 of the specification.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from config.settings import load_taxonomy
from .image_analyzer import VisualAnalysisResult, VisualConceptItem


class ClaimComparisonResult(BaseModel):
    reported_problem: str
    observed_problem: str
    match_status: str  # "MATCH" | "MISMATCH" | "UNCERTAIN" | "NO_MEDIA"
    confidence: float
    reason: str


class MediaRelevanceResult(BaseModel):
    provided: bool
    media_type: Optional[str] = None  # "image" | "video" | None
    visual_analysis: Optional[VisualAnalysisResult] = None
    claim_comparison: ClaimComparisonResult
    frames_checked: int = 0


class MediaComparator:
    def __init__(self):
        self.taxonomy = load_taxonomy()

    def compare(
        self,
        reported_category: str,
        reported_problem: str,
        visual_analysis: Optional[VisualAnalysisResult],
        media_type: Optional[str] = "image",
        frames_checked: int = 1
    ) -> MediaRelevanceResult:
        # Case 1: No media provided
        if visual_analysis is None:
            return MediaRelevanceResult(
                provided=False,
                media_type=None,
                visual_analysis=None,
                claim_comparison=ClaimComparisonResult(
                    reported_problem=reported_problem or "Unspecified",
                    observed_problem="None",
                    match_status="NO_MEDIA",
                    confidence=0.0,
                    reason="No image or video was provided."
                ),
                frames_checked=0
            )

        observed_problem = visual_analysis.top_problem_type
        observed_category = visual_analysis.top_category
        top_concept_label = (
            visual_analysis.visual_concepts[0].label
            if visual_analysis.visual_concepts
            else "unidentified scene"
        )
        top_conf = (
            visual_analysis.visual_concepts[0].confidence
            if visual_analysis.visual_concepts
            else 0.85
        )

        # Case 2: Blurry / low-quality image
        if visual_analysis.is_blurry:
            conf = round(float(min(0.58, max(0.35, 0.40 + visual_analysis.sharpness_score / 300.0))), 2)
            prob_label = reported_problem.lower() if reported_problem and reported_problem.lower() != "other" else "civic problem"
            reason = f"The image may contain relevant {prob_label}, but image quality prevents confident visual interpretation."
            return MediaRelevanceResult(
                provided=True,
                media_type=media_type,
                visual_analysis=visual_analysis,
                claim_comparison=ClaimComparisonResult(
                    reported_problem=reported_problem,
                    observed_problem=f"Unclear / Blurry ({observed_problem})",
                    match_status="UNCERTAIN",
                    confidence=conf,
                    reason=reason
                ),
                frames_checked=frames_checked
            )

        # Case 3: Unrelated content (cartoons, fictional characters, selfie, indoor, documents)
        if visual_analysis.unrelated_content:
            conf = max(0.92, top_conf)
            if "fictional" in top_concept_label.lower() or "character" in top_concept_label.lower():
                reason = f"The complaint describes {reported_problem.lower()}, but the uploaded image depicts a fictional character or artwork and does not visibly show {reported_problem.lower()} or civic defect."
            elif "portrait" in top_concept_label.lower():
                reason = f"The complaint describes {reported_problem.lower()}, but the uploaded image depicts a personal portrait or selfie rather than civic infrastructure."
            else:
                reason = f"The complaint describes {reported_problem.lower()}, but the uploaded image depicts {top_concept_label} (unrelated non-civic content)."

            return MediaRelevanceResult(
                provided=True,
                media_type=media_type,
                visual_analysis=visual_analysis,
                claim_comparison=ClaimComparisonResult(
                    reported_problem=reported_problem,
                    observed_problem=observed_problem,
                    match_status="MISMATCH",
                    confidence=round(conf, 2),
                    reason=reason
                ),
                frames_checked=frames_checked
            )

        # Normalize categories for comparison
        reported_cat_clean = self.taxonomy.normalize_category_name(reported_category).lower()
        observed_cat_clean = self.taxonomy.normalize_category_name(observed_category).lower()

        # Check semantic consistency between reported claim and observed concepts
        is_category_match = (
            reported_cat_clean == observed_cat_clean
            or reported_cat_clean in observed_cat_clean
            or observed_cat_clean in reported_cat_clean
        )

        # Also check cross-domain alignment (e.g. waterlogging reported under Water Supply or Roads)
        if "water" in reported_cat_clean and "water" in observed_cat_clean:
            is_category_match = True
        if "road" in reported_cat_clean and ("pothole" in top_concept_label or "road" in top_concept_label):
            is_category_match = True
        if "sanitation" in reported_cat_clean and ("garbage" in top_concept_label or "drain" in top_concept_label or "sewage" in top_concept_label):
            is_category_match = True
        if "electr" in reported_cat_clean and ("wire" in top_concept_label or "electr" in top_concept_label or "transformer" in top_concept_label):
            is_category_match = True
        if "safety" in reported_cat_clean and ("streetlight" in top_concept_label or "fire" in top_concept_label or "accident" in top_concept_label):
            is_category_match = True

        # Check problem-level match
        rep_prob_lower = reported_problem.lower()
        obs_prob_lower = observed_problem.lower()
        is_problem_match = (
            rep_prob_lower in obs_prob_lower
            or obs_prob_lower in rep_prob_lower
            or any(w in obs_prob_lower for w in rep_prob_lower.split() if len(w) > 3)
        )

        if is_category_match and (is_problem_match or top_conf >= 0.70):
            # Case 4: Semantically consistent match
            conf = round(float(min(0.98, max(0.80, top_conf))), 2)
            reason = f"The image visibly contains {top_concept_label}, consistent with the reported {reported_problem} ({reported_category})."
            match_status = "MATCH"
        elif is_category_match and top_conf < 0.70:
            # Related domain but low concept confidence
            conf = round(float(top_conf), 2)
            reason = f"The image shows visual elements resembling {observed_category}, but does not clearly depict {reported_problem}."
            match_status = "UNCERTAIN"
        else:
            # Case 5: Mismatch between reported issue and observed civic object
            # (e.g. Broken streetlight reported, but image is a pothole)
            conf = round(float(max(0.88, top_conf)), 2)
            reason = f"The complaint describes {reported_problem} ({reported_category}), but the uploaded image visibly shows {top_concept_label} ({observed_category})."
            match_status = "MISMATCH"

        return MediaRelevanceResult(
            provided=True,
            media_type=media_type,
            visual_analysis=visual_analysis,
            claim_comparison=ClaimComparisonResult(
                reported_problem=reported_problem,
                observed_problem=observed_problem,
                match_status=match_status,
                confidence=conf,
                reason=reason
            ),
            frames_checked=frames_checked
        )
