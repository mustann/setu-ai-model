"""
Strict Output Schemas for Report Structuring & Classification AI (SIH 2026).
Adheres strictly to Section 17 of the Master Prompt Specification.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class AlternateCategorySchema(BaseModel):
    category: str
    confidence: float


class DomainClassificationSchema(BaseModel):
    category: str
    problem_type: str
    confidence: float
    alternate_categories: List[AlternateCategorySchema] = Field(default_factory=list)
    reason: str


class SeveritySchema(BaseModel):
    level: str  # "Low" | "Medium" | "High" | "Critical"
    confidence: float
    signals: List[str] = Field(default_factory=list)
    reason: str


class CompletenessSchema(BaseModel):
    score: float
    missing_fields: List[str] = Field(default_factory=list)
    suggestions_for_citizen: List[str] = Field(default_factory=list)


class VisualConceptItemSchema(BaseModel):
    label: str
    confidence: float


class VisualAnalysisSchema(BaseModel):
    visual_description: str
    visual_concepts: List[VisualConceptItemSchema] = Field(default_factory=list)
    unrelated_content: bool = False


class ClaimComparisonSchema(BaseModel):
    reported_problem: str
    observed_problem: str
    match_status: str  # "MATCH" | "MISMATCH" | "UNCERTAIN" | "NO_MEDIA"
    confidence: float
    reason: str


class MediaRelevanceSchema(BaseModel):
    provided: bool
    media_type: Optional[str] = None  # "image" | "video" | None
    visual_analysis: Optional[VisualAnalysisSchema] = None
    claim_comparison: ClaimComparisonSchema
    frames_checked: int = 0

    # Backward-compatible convenience properties
    @property
    def match(self) -> bool:
        return self.claim_comparison.match_status == "MATCH"

    @property
    def confidence(self) -> float:
        return self.claim_comparison.confidence

    @property
    def justification(self) -> str:
        return self.claim_comparison.reason


class ProcessingMetadataSchema(BaseModel):
    model_versions: Dict[str, str] = Field(default_factory=dict)
    processing_time_ms: float = 0.0
    offline_mode_used: bool = True


class StructuredReportOutput(BaseModel):
    report_id: str
    domain_classification: DomainClassificationSchema
    severity: SeveritySchema
    completeness: CompletenessSchema
    media_relevance: MediaRelevanceSchema
    requires_human_review: bool
    overall_confidence: float
    processing_metadata: ProcessingMetadataSchema

    def to_model2_contract(self) -> Dict[str, Any]:
        """
        Exports data conforming to the Section 21 Model 2 Integration Contract.
        """
        visual_desc = (
            self.media_relevance.visual_analysis.visual_description
            if self.media_relevance.visual_analysis
            else None
        )
        visual_concepts = (
            [
                {"label": c.label, "confidence": c.confidence}
                for c in self.media_relevance.visual_analysis.visual_concepts
            ]
            if self.media_relevance.visual_analysis
            else []
        )
        return {
            "reported_domain": self.domain_classification.category,
            "reported_problem": self.domain_classification.problem_type,
            "media_visual_description": visual_desc,
            "media_visual_concepts": visual_concepts,
            "media_match_status": self.media_relevance.claim_comparison.match_status,
            "media_match_confidence": self.media_relevance.claim_comparison.confidence
        }
