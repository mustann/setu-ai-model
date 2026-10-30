"""
Visual Concepts Taxonomy loader and models (SIH 2026).
Defines observable civic visual concepts and unrelated/negative concepts
configured via YAML per Section 5 of the specification.
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
import yaml
from pydantic import BaseModel, Field

from config.settings import VISUAL_CONCEPTS_PATH


class VisualConcept(BaseModel):
    id: str
    label: str
    category: str
    problem_type: str
    description: str = ""
    clip_prompts: List[str] = Field(default_factory=list)
    is_unrelated: bool = False


class VisualConceptTaxonomy(BaseModel):
    version: str = "1.0.0"
    concepts: List[VisualConcept]

    def get_civic_concepts(self) -> List[VisualConcept]:
        return [c for c in self.concepts if not c.is_unrelated]

    def get_unrelated_concepts(self) -> List[VisualConcept]:
        return [c for c in self.concepts if c.is_unrelated]

    def get_by_label(self, label: str) -> Optional[VisualConcept]:
        target = label.strip().lower()
        for c in self.concepts:
            if c.label.lower() == target or c.id.lower() == target:
                return c
        return None

    def get_by_id(self, concept_id: str) -> Optional[VisualConcept]:
        for c in self.concepts:
            if c.id.lower() == concept_id.strip().lower():
                return c
        return None


def load_visual_taxonomy(path: Path = VISUAL_CONCEPTS_PATH) -> VisualConceptTaxonomy:
    if not path.exists():
        raise FileNotFoundError(f"Visual concepts taxonomy not found at: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return VisualConceptTaxonomy(**data)
