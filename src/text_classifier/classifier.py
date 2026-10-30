"""
Text Classification Pipeline for Civic Problem Intelligence (Model 1).
Provides independent text understanding without image bias:
- Categorical domain classification (configurable taxonomy)
- Fine-grained problem_type identification
- Explainable classification reasoning
- Alternate candidate categories with calibrated confidences
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
import joblib
import numpy as np
from pydantic import BaseModel, Field

from config.settings import MODELS_DIR, load_taxonomy, Taxonomy, settings
from .train import train_and_save_classifier
from .taxonomy import TextTaxonomyHelper


class AlternateCategory(BaseModel):
    category: str
    confidence: float


class DomainResult(BaseModel):
    category: str
    problem_type: str
    confidence: float
    alternate_categories: List[AlternateCategory] = Field(default_factory=list)
    reason: str


class TextClassifier:
    def __init__(self, model_path: Optional[Path] = None, taxonomy: Optional[Taxonomy] = None):
        self.model_path = model_path or (MODELS_DIR / "text_classifier.joblib")
        self.taxonomy = taxonomy or load_taxonomy()
        self.helper = TextTaxonomyHelper(taxonomy=self.taxonomy)
        self.model = self._load_or_train_model()

    def _load_or_train_model(self):
        if not self.model_path.exists():
            print(f"Model file not found at {self.model_path}. Training new classifier...")
            return train_and_save_classifier(self.model_path)
        return joblib.load(self.model_path)

    def _apply_keyword_boost(self, text: str, class_probs: Dict[str, float]) -> Dict[str, float]:
        """
        Calculates domain keyword cues (including Hinglish/regional terms) to refine probabilities.
        Applies multiplicative weighting and softmax temperature scaling.
        """
        text_lower = text.lower()
        boosted_scores = {}

        for cat in self.taxonomy.categories:
            canonical_name = self.taxonomy.normalize_category_name(cat.name)
            matches = 0
            for kw in cat.keywords:
                pattern = r"\b" + re.escape(kw.lower()) + r"\b"
                if re.search(pattern, text_lower):
                    matches += 1

            # Match against problem type keywords as well
            for pt in cat.problem_types:
                for kw in pt.keywords:
                    pattern = r"\b" + re.escape(kw.lower()) + r"\b"
                    if re.search(pattern, text_lower):
                        matches += 1.5

            prior_prob = class_probs.get(canonical_name, 0.01)
            weight = 1.0 + (matches * 1.8)
            boosted_scores[canonical_name] = prior_prob * weight

        # Temperature sharpening
        logits = np.array(list(boosted_scores.values()))
        if logits.sum() > 0:
            probs = logits / logits.sum()
            scaled = np.power(probs, 1.4)
            scaled /= scaled.sum()
        else:
            scaled = np.ones_like(logits) / len(logits)

        result = {}
        for i, cat_name in enumerate(boosted_scores.keys()):
            result[cat_name] = float(round(scaled[i], 4))

        return result

    def _classify_offline(self, text: str) -> DomainResult:
        if not text or not text.strip():
            return DomainResult(
                category=self.taxonomy.default_category,
                problem_type="General Civic Grievance",
                confidence=0.10,
                alternate_categories=[],
                reason="No complaint text provided; assigned default category with minimum confidence."
            )

        classes = list(self.model.classes_)
        raw_probs = self.model.predict_proba([text])[0]

        # Aggregate raw probs by normalized canonical category names
        prob_dict: Dict[str, float] = {}
        for i, cls_name in enumerate(classes):
            canonical = self.taxonomy.normalize_category_name(cls_name)
            prob_dict[canonical] = prob_dict.get(canonical, 0.0) + float(raw_probs[i])

        # Apply keyword enhancement
        boosted_probs = self._apply_keyword_boost(text, prob_dict)

        # Sort categories by confidence descending
        sorted_cats = sorted(boosted_probs.items(), key=lambda x: x[1], reverse=True)

        top_cat, top_conf = sorted_cats[0]
        alternates = [
            AlternateCategory(category=cat, confidence=round(float(conf), 4))
            for cat, conf in sorted_cats[1:4]
        ]

        # Extract fine-grained problem type and explainable reason
        problem_type, pt_conf, reason = self.helper.extract_problem_type(top_cat, text)

        # Blended calibrated confidence
        final_conf = round(float(np.clip(top_conf * 0.8 + pt_conf * 0.2, 0.15, 0.98)), 4)

        return DomainResult(
            category=top_cat,
            problem_type=problem_type,
            confidence=final_conf,
            alternate_categories=alternates,
            reason=reason
        )

    def _classify_online_llm(self, text: str) -> DomainResult:
        # Fallback to offline classifier for deterministic, fast offline mode
        return self._classify_offline(text)

    def classify(self, text: str, force_offline: Optional[bool] = None) -> DomainResult:
        use_offline = force_offline if force_offline is not None else settings.offline_mode
        if use_offline:
            return self._classify_offline(text)
        else:
            return self._classify_online_llm(text)
