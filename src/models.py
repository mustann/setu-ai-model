"""
Data Models and Model 2 Integration Contract (SIH 2026).
Defines the clean handoff boundary between Model 1 (Structuring & Classification)
and downstream Model 2 (Evidence Trust / Suspicious-Content Flagging).
Model 1 MUST NOT compute trust scores, authenticity scores, fraud probabilities,
or EXIF metadata tampering scores.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class MediaVisualConceptItem(BaseModel):
    label: str
    confidence: float


class Model2HandoffContract(BaseModel):
    """
    Section 21: Model 2 Integration Contract.
    Exposes Model 1's structured understanding to Model 2.
    Model 2 subsequently performs:
    - duplicate / near-duplicate detection (pHash)
    - stock/reused image heuristics
    - EXIF analysis & tampering checks
    - GPS consistency & timestamp consistency
    - behavioral analysis & fraud probability
    """
    reported_domain: str
    reported_problem: str
    media_visual_description: Optional[str] = None
    media_visual_concepts: List[MediaVisualConceptItem] = Field(default_factory=list)
    media_match_status: str  # "MATCH" | "MISMATCH" | "UNCERTAIN" | "NO_MEDIA"
    media_match_confidence: float
