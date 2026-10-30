"""
Pydantic schemas adhering strictly to Section 5 of the Master Build Specification.
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class AlternateCategory(BaseModel):
    category: str
    confidence: float


class DomainClassification(BaseModel):
    category: str
    confidence: float
    alternate_categories: List[AlternateCategory] = Field(default_factory=list)
    justification: str


class SeverityResult(BaseModel):
    level: Literal["Low", "Medium", "High", "Critical"]
    confidence: float
    signals: List[str] = Field(default_factory=list)
    justification: str


class CompletenessResult(BaseModel):
    score: float
    missing_fields: List[str] = Field(default_factory=list)
    suggestions_for_citizen: List[str] = Field(default_factory=list)
    justification: str


class MediaRelevanceResult(BaseModel):
    provided: bool = False
    match: Optional[bool] = None  # None when no media provided; True/False/None (unclear)
    confidence: float = 0.0
    justification: str
    frames_checked: int = 0


class ProcessingMetadata(BaseModel):
    model_versions: Dict[str, str] = Field(default_factory=dict)
    processing_time_ms: int = 0
    offline_mode_used: bool = True


class StructuredReportOutput(BaseModel):
    report_id: str
    domain_classification: DomainClassification
    severity: SeverityResult
    completeness: CompletenessResult
    media_relevance: MediaRelevanceResult
    requires_human_review: bool = True
    overall_confidence: float
    processing_metadata: ProcessingMetadata


# Input Schema for programmatic / JSON requests
class ReportInputRequest(BaseModel):
    text: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    timestamp: Optional[str] = None
