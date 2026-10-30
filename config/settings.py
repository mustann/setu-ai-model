import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import yaml
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
DATA_DIR = BASE_DIR / "data"
TAXONOMY_PATH = CONFIG_DIR / "taxonomy.yaml"
VISUAL_CONCEPTS_PATH = CONFIG_DIR / "visual_concepts.yaml"
SYNTHETIC_DATA_PATH = DATA_DIR / "synthetic_reports.json"
DEMO_ASSETS_DIR = DATA_DIR / "demo_assets"
MODELS_DIR = BASE_DIR / "models"


class ProblemTypeConfig(BaseModel):
    name: str
    keywords: List[str] = Field(default_factory=list)
    description: str = ""


class CategoryConfig(BaseModel):
    id: str
    name: str
    aliases: List[str] = Field(default_factory=list)
    description: str
    problem_types: List[ProblemTypeConfig] = Field(default_factory=list)
    clip_prompts: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)


class Taxonomy(BaseModel):
    version: str
    default_category: str
    categories: List[CategoryConfig]

    def get_category_names(self) -> List[str]:
        return [c.name for c in self.categories]

    def normalize_category_name(self, name: str) -> str:
        """
        Normalizes any category name, alias, or id to canonical category name.
        e.g. 'Roads & Infrastructure' -> 'Roads / Infrastructure'
        """
        if not name:
            return self.default_category
        cat = self.get_by_name(name)
        return cat.name if cat else name

    def get_by_name(self, name: str) -> Optional[CategoryConfig]:
        if not name:
            return None
        target = name.strip().lower()
        # Direct name or id match
        for c in self.categories:
            if c.name.lower() == target or c.id.lower() == target:
                return c
        # Alias match
        for c in self.categories:
            for alias in c.aliases:
                if alias.lower() == target:
                    return c
        # Fuzzy match for '&' vs '/'
        target_clean = target.replace("&", "/").replace("and", "/").replace("  ", " ").strip()
        for c in self.categories:
            c_clean = c.name.lower().replace("&", "/").replace("and", "/").replace("  ", " ").strip()
            if c_clean == target_clean:
                return c
        return None

    def detect_problem_type(self, category_name: str, text: str) -> Tuple[str, float, str]:
        """
        Identifies the specific problem type within a category based on the citizen's complaint text.
        Returns: (problem_type, confidence, reason)
        """
        cat = self.get_by_name(category_name)
        if not cat or not cat.problem_types:
            return "General Civic Grievance", 0.60, f"Classified under '{category_name}'."

        text_lower = text.lower() if text else ""
        best_pt: Optional[ProblemTypeConfig] = None
        best_score = 0

        for pt in cat.problem_types:
            score = 0
            for kw in pt.keywords:
                pattern = r"\b" + re.escape(kw.lower()) + r"\b"
                if re.search(pattern, text_lower):
                    score += 2
                elif kw.lower() in text_lower:
                    score += 1
            if score > best_score:
                best_score = score
                best_pt = pt

        if best_pt and best_score > 0:
            conf = min(0.96, 0.80 + best_score * 0.05)
            reason = f"The complaint explicitly describes {best_pt.name.lower()} consistent with {cat.name}."
            return best_pt.name, round(conf, 2), reason
        else:
            # Fallback to first problem type or standard label
            default_pt = cat.problem_types[0].name
            return default_pt, 0.70, f"The complaint details indicate an issue within {cat.name}."


def load_taxonomy(path: Path = TAXONOMY_PATH) -> Taxonomy:
    if not path.exists():
        raise FileNotFoundError(f"Taxonomy config not found at: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return Taxonomy(**data)


class AppSettings(BaseModel):
    app_name: str = "SIH 2026 Civic Intelligence - Report Structuring & Classification AI"
    version: str = "1.1.0"
    offline_mode: bool = True
    human_review_confidence_threshold: float = 0.70
    completeness_min_threshold: float = 0.50
    blur_laplacian_threshold: float = 80.0
    text_model_type: str = "calibrated_classifier"
    clip_model_name: str = "openai/clip-vit-base-patch32"


settings = AppSettings()
