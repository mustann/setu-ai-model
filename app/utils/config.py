"""
Configuration and Taxonomy loader for Report Structuring & Classification AI.
"""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
import yaml
from pydantic import BaseModel, Field

# Base Directory Resolution
BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = BASE_DIR / "config"
TAXONOMY_PATH = CONFIG_DIR / "taxonomy.yaml"
DATA_DIR = BASE_DIR / "data"
DEMO_ASSETS_DIR = DATA_DIR / "demo_assets"


class ProblemType(BaseModel):
    name: str
    keywords: List[str] = Field(default_factory=list)
    description: Optional[str] = None


class CategoryItem(BaseModel):
    id: Optional[str] = None
    name: str
    aliases: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    problem_types: List[ProblemType] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)


class Taxonomy(BaseModel):
    version: str = "1.0.0"
    default_category: str = "Other"
    categories: List[CategoryItem] = Field(default_factory=list)

    def get_category_names(self) -> List[str]:
        return [c.name for c in self.categories]

    def normalize_category_name(self, name: str) -> str:
        name_clean = name.strip().lower().replace(" ", "").replace("/", "").replace("&", "and")
        for cat in self.categories:
            c_clean = cat.name.strip().lower().replace(" ", "").replace("/", "").replace("&", "and")
            if name_clean == c_clean:
                return cat.name
            for alias in cat.aliases:
                a_clean = alias.strip().lower().replace(" ", "").replace("/", "").replace("&", "and")
                if name_clean == a_clean:
                    return cat.name
        return self.default_category


def load_taxonomy(path: Path = TAXONOMY_PATH) -> Taxonomy:
    """Loads taxonomy categories dynamically from YAML configuration."""
    if not path.exists():
        # Fallback default taxonomy as per Section 3
        default_categories = [
            CategoryItem(name="Water Supply", aliases=["Water Supply & Drainage"]),
            CategoryItem(name="Electricity", aliases=["Power & Electricity"]),
            CategoryItem(name="Roads/Infrastructure", aliases=["Roads / Infrastructure", "Roads"]),
            CategoryItem(name="Sanitation/Waste", aliases=["Sanitation & Waste", "Sanitation"]),
            CategoryItem(name="Public Health", aliases=["Health"]),
            CategoryItem(name="Education Infrastructure", aliases=["Education"]),
            CategoryItem(name="Public Safety", aliases=["Safety"]),
            CategoryItem(name="Other", aliases=[])
        ]
        return Taxonomy(categories=default_categories)

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Support simple list of string categories or structured CategoryItem dicts
    cats = []
    raw_cats = data.get("categories", [])
    for item in raw_cats:
        if isinstance(item, str):
            cats.append(CategoryItem(name=item))
        elif isinstance(item, dict):
            cats.append(CategoryItem(**item))

    return Taxonomy(
        version=data.get("version", "1.0.0"),
        default_category=data.get("default_category", "Other"),
        categories=cats
    )


class AppSettings(BaseModel):
    app_name: str = "Report Structuring & Classification AI"
    version: str = "1.0.0"
    environment: str = os.getenv("ENVIRONMENT", "development")
    offline_mode: bool = os.getenv("OFFLINE_MODE", "true").lower() in ("true", "1", "yes")
    human_review_confidence_threshold: float = float(os.getenv("HUMAN_REVIEW_CONFIDENCE_THRESHOLD", "0.75"))
    completeness_min_threshold: float = 0.50
    text_classifier_mode: str = os.getenv("TEXT_CLASSIFIER_MODE", "auto")
    llm_api_key: Optional[str] = os.getenv("LLM_API_KEY", None)
    vision_api_key: Optional[str] = os.getenv("VISION_API_KEY", None)
    text_model: Optional[str] = os.getenv("TEXT_MODEL", None)
    vision_model: Optional[str] = os.getenv("VISION_MODEL", None)


settings = AppSettings()
taxonomy = load_taxonomy()
