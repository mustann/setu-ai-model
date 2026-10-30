"""
Taxonomy helper module for Text Classification.
Exports category configurations, problem types, and mapping helpers.
"""

from typing import List, Optional, Tuple
from config.settings import Taxonomy, CategoryConfig, ProblemTypeConfig, load_taxonomy


class TextTaxonomyHelper:
    def __init__(self, taxonomy: Optional[Taxonomy] = None):
        self.taxonomy = taxonomy or load_taxonomy()

    def get_categories(self) -> List[str]:
        return self.taxonomy.get_category_names()

    def normalize_category(self, category_name: str) -> str:
        return self.taxonomy.normalize_category_name(category_name)

    def extract_problem_type(self, category: str, text: str) -> Tuple[str, float, str]:
        """
        Determines the specific problem type and generates an explainable reasoning string.
        """
        return self.taxonomy.detect_problem_type(category, text)
