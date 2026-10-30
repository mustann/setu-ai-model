"""
Orchestration Pipeline for Report Structuring & Classification AI (SIH 2026).
Coordinates multi-modal stages adhering strictly to Model 1 pipeline boundary:
1. Independent Text Understanding (Category, Problem Type, Reason)
2. Severity Estimation (Level, Signals, Reason)
3. Completeness Evaluation (Missing Fields, Citizen Guidance)
4. Independent Visual Observation (Concepts, Description, Unrelated Flag)
5. Semantic Text <-> Media Claim Comparison (MATCH, MISMATCH, UNCERTAIN, NO_MEDIA)
6. Advisory Decision Flag (requires_human_review) & Model 2 Integration Handoff
"""

import asyncio
import time
import uuid
from typing import List, Optional, Union
from PIL import Image

from config.settings import settings, load_taxonomy, Taxonomy
from src.text_classifier.classifier import TextClassifier
from src.severity_scorer.scorer import SeverityScorer
from src.completeness_scorer.scorer import CompletenessScorer
from src.vision_checker.clip_checker import VisionChecker
from .schemas import (
    StructuredReportOutput,
    DomainClassificationSchema,
    AlternateCategorySchema,
    SeveritySchema,
    CompletenessSchema,
    MediaRelevanceSchema,
    VisualAnalysisSchema,
    VisualConceptItemSchema,
    ClaimComparisonSchema,
    ProcessingMetadataSchema,
)


class ReportOrchestrator:
    def __init__(self, taxonomy: Optional[Taxonomy] = None):
        self.taxonomy = taxonomy or load_taxonomy()
        self.text_classifier = TextClassifier(taxonomy=self.taxonomy)
        self.severity_scorer = SeverityScorer()
        self.completeness_scorer = CompletenessScorer()
        self.vision_checker = VisionChecker(taxonomy=self.taxonomy)

    def _compute_overall_confidence(
        self,
        domain_conf: float,
        severity_conf: float,
        completeness_score: float,
        media_match_status: str,
        media_relevance_conf: float,
        has_media: bool
    ) -> float:
        """
        Synthesizes composite overall confidence without obscuring media mismatches (Section 18).
        """
        if has_media:
            if media_match_status == "MISMATCH":
                # Media mismatch indicates dispute between claim and evidence.
                # Cap overall automated confidence to prevent hiding the discrepancy.
                base = (domain_conf * 0.40 + severity_conf * 0.20 + completeness_score * 0.20)
                return round(float(min(0.50, base * 0.6)), 4)
            elif media_match_status == "UNCERTAIN":
                base = (domain_conf * 0.40 + severity_conf * 0.25 + completeness_score * 0.20 + media_relevance_conf * 0.15)
                return round(float(min(0.65, base * 0.8)), 4)
            else:
                # MATCH
                score = (
                    domain_conf * 0.40 +
                    severity_conf * 0.25 +
                    completeness_score * 0.20 +
                    media_relevance_conf * 0.15
                )
                return round(float(min(1.0, max(0.05, score))), 4)
        else:
            # NO_MEDIA: Rebalance based on text, severity, completeness
            score = (
                domain_conf * 0.50 +
                severity_conf * 0.30 +
                completeness_score * 0.20
            )
            return round(float(min(1.0, max(0.05, score))), 4)

    def _determine_human_review(
        self,
        overall_confidence: float,
        severity_level: str,
        media_provided: bool,
        media_match_status: str,
        completeness_score: float
    ) -> bool:
        """
        Section 19: Model 1 Advisory Decision Rule.
        Never automatically rejects or closes reports.
        Requires human review if:
        - Media provided but status is MISMATCH or UNCERTAIN
        - Severity is Critical (urgent safety hazard requires officer dispatch)
        - Completeness is critically low (< 0.50)
        - Overall composite confidence < threshold (0.70)
        """
        if media_provided and media_match_status in ["MISMATCH", "UNCERTAIN"]:
            return True
        if severity_level == "Critical":
            return True
        if overall_confidence < settings.human_review_confidence_threshold:
            return True
        if completeness_score < settings.completeness_min_threshold:
            return True
        return False

    async def process_report(
        self,
        text: str,
        media_items: Optional[List[Union[Image.Image, bytes, str]]] = None,
        location: Optional[str] = None,
        timestamp: Optional[str] = None,
        report_id: Optional[str] = None,
        is_video: bool = False,
        offline_mode: Optional[bool] = None
    ) -> StructuredReportOutput:
        t0 = time.perf_counter()
        use_offline = offline_mode if offline_mode is not None else settings.offline_mode
        report_id = report_id or f"REP-{int(time.time())}-{uuid.uuid4().hex[:6].upper()}"
        media_items = media_items or []
        media_count = len(media_items)

        loop = asyncio.get_running_loop()

        # Step 1: Independent Text Classification (Domain & Problem Type)
        domain_task = loop.run_in_executor(
            None, self.text_classifier.classify, text, use_offline
        )
        completeness_task = loop.run_in_executor(
            None, self.completeness_scorer.evaluate, text, media_count, location, timestamp
        )

        domain_res, completeness_res = await asyncio.gather(domain_task, completeness_task)

        # Step 2: Severity Scorer & Independent Media Sanity Checker
        severity_task = loop.run_in_executor(
            None, self.severity_scorer.evaluate, text, domain_res.category
        )
        vision_task = loop.run_in_executor(
            None,
            self.vision_checker.evaluate_media,
            media_items,
            domain_res.category,
            domain_res.problem_type,
            is_video
        )

        severity_res, vision_res = await asyncio.gather(severity_task, vision_task)

        # Step 3: Synthesis of overall confidence and advisory decision
        match_status = vision_res.claim_comparison.match_status
        overall_conf = self._compute_overall_confidence(
            domain_conf=domain_res.confidence,
            severity_conf=severity_res.confidence,
            completeness_score=completeness_res.score,
            media_match_status=match_status,
            media_relevance_conf=vision_res.claim_comparison.confidence,
            has_media=vision_res.provided
        )

        requires_review = self._determine_human_review(
            overall_confidence=overall_conf,
            severity_level=severity_res.level,
            media_provided=vision_res.provided,
            media_match_status=match_status,
            completeness_score=completeness_res.score
        )

        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)

        # Step 4: Construct Section 17 Output Schema
        visual_analysis_schema = None
        if vision_res.visual_analysis:
            visual_analysis_schema = VisualAnalysisSchema(
                visual_description=vision_res.visual_analysis.visual_description,
                visual_concepts=[
                    VisualConceptItemSchema(label=c.label, confidence=c.confidence)
                    for c in vision_res.visual_analysis.visual_concepts
                ],
                unrelated_content=vision_res.visual_analysis.unrelated_content
            )

        claim_comp_schema = ClaimComparisonSchema(
            reported_problem=vision_res.claim_comparison.reported_problem,
            observed_problem=vision_res.claim_comparison.observed_problem,
            match_status=vision_res.claim_comparison.match_status,
            confidence=vision_res.claim_comparison.confidence,
            reason=vision_res.claim_comparison.reason
        )

        output = StructuredReportOutput(
            report_id=report_id,
            domain_classification=DomainClassificationSchema(
                category=domain_res.category,
                problem_type=domain_res.problem_type,
                confidence=domain_res.confidence,
                alternate_categories=[
                    AlternateCategorySchema(category=alt.category, confidence=alt.confidence)
                    for alt in domain_res.alternate_categories
                ],
                reason=domain_res.reason
            ),
            severity=SeveritySchema(
                level=severity_res.level,
                confidence=severity_res.confidence,
                signals=severity_res.signals,
                reason=severity_res.reason
            ),
            completeness=CompletenessSchema(
                score=completeness_res.score,
                missing_fields=completeness_res.missing_fields,
                suggestions_for_citizen=completeness_res.suggestions_for_citizen
            ),
            media_relevance=MediaRelevanceSchema(
                provided=vision_res.provided,
                media_type=vision_res.media_type,
                visual_analysis=visual_analysis_schema,
                claim_comparison=claim_comp_schema,
                frames_checked=vision_res.frames_checked
            ),
            requires_human_review=requires_review,
            overall_confidence=overall_conf,
            processing_metadata=ProcessingMetadataSchema(
                model_versions={
                    "text_classifier": "TFIDF-LogisticCalibrated-v1.1",
                    "vision_checker": "CLIP-ViT-B32-ZeroShot-v1.1",
                    "severity_scorer": "SignalRegex-Hybrid-v1.1",
                    "completeness_scorer": "WeightedRule-v1.1"
                },
                processing_time_ms=elapsed_ms,
                offline_mode_used=use_offline
            )
        )

        return output
