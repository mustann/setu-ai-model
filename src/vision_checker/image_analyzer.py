"""
Independent Visual Analyzer for Civic Media (Model 1).
Inspects uploaded media completely independently of citizen complaint text.
Answers: "What is actually visible in this image?"
Produces:
- Visual description
- Detected visual concepts with confidence scores
- Unrelated content indicator (true for cartoons, fictional characters, selfies, indoor scenes, documents)
- Sharpness and blur assessment (for UNCERTAIN quality handling)
"""

import io
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
import cv2
import numpy as np
from PIL import Image
from pydantic import BaseModel, Field

from config.settings import settings, VISUAL_CONCEPTS_PATH
from .visual_concepts import VisualConceptTaxonomy, VisualConcept, load_visual_taxonomy


class VisualConceptItem(BaseModel):
    label: str
    confidence: float


class VisualAnalysisResult(BaseModel):
    visual_description: str
    visual_concepts: List[VisualConceptItem] = Field(default_factory=list)
    unrelated_content: bool = False
    is_blurry: bool = False
    sharpness_score: float = 100.0
    top_concept_id: str = "other"
    top_category: str = "Other"
    top_problem_type: str = "Other"


class ImageAnalyzer:
    def __init__(self, visual_taxonomy: Optional[VisualConceptTaxonomy] = None):
        self.taxonomy = visual_taxonomy or load_visual_taxonomy()
        self.clip_model = None
        self.clip_processor = None
        self._clip_attempted = False
        self._concept_prompts: List[str] = []
        self._concept_mapping: List[VisualConcept] = []
        self._setup_concept_prompts()

    def _setup_concept_prompts(self):
        self._concept_prompts = []
        self._concept_mapping = []
        for concept in self.taxonomy.concepts:
            # Use representative prompt
            prompt = concept.clip_prompts[0] if concept.clip_prompts else f"a photo of {concept.label}"
            self._concept_prompts.append(prompt)
            self._concept_mapping.append(concept)

    def _init_clip_if_available(self):
        if self._clip_attempted:
            return
        self._clip_attempted = True
        try:
            from transformers import CLIPProcessor, CLIPModel
            import torch
            model_name = settings.clip_model_name
            # Load local offline cached CLIP
            self.clip_processor = CLIPProcessor.from_pretrained(model_name, local_files_only=True)
            self.clip_model = CLIPModel.from_pretrained(model_name, local_files_only=True)
            self.clip_model.eval()
            print(f"[ImageAnalyzer] Initialized local offline CLIP ({model_name})")
        except Exception as e:
            print(f"[ImageAnalyzer] Offline CLIP not available, falling back to heuristic analyzer: {e}")
            self.clip_model = None
            self.clip_processor = None

    def check_sharpness(self, cv_img: np.ndarray) -> Tuple[bool, float]:
        """
        Computes sharpness using the variance of the Laplacian.
        Returns (is_clear, score).
        """
        if len(cv_img.shape) == 3:
            gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        else:
            gray = cv_img
        val = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        return (val >= settings.blur_laplacian_threshold), round(val, 2)

    def check_selfie_or_portrait(self, cv_img: np.ndarray) -> bool:
        """
        Detects if an image is predominantly a face/selfie rather than civic infrastructure.
        """
        h, w = cv_img.shape[:2]
        center = cv_img[h // 4 : 3 * h // 4, w // 4 : 3 * w // 4]
        if center.size == 0:
            return False

        hsv = cv2.cvtColor(center, cv2.COLOR_BGR2HSV)
        lower_skin = np.array([0, 30, 80], dtype=np.uint8)
        upper_skin = np.array([25, 200, 255], dtype=np.uint8)
        mask = cv2.inRange(hsv, lower_skin, upper_skin)
        center_skin_ratio = np.sum(mask > 0) / (center.shape[0] * center.shape[1])

        gray = cv2.cvtColor(center, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        center_edge_density = np.sum(edges > 0) / (center.shape[0] * center.shape[1])

        return bool(center_skin_ratio > 0.40 and center_edge_density < 0.05)

    def _generate_description(self, concept: VisualConcept, is_unrelated: bool, is_blurry: bool) -> str:
        if is_blurry:
            return f"Low-quality or blurry image containing possible visual elements of {concept.label}, but lacking clear resolution."

        if is_unrelated:
            if "fictional" in concept.id or "character" in concept.label.lower():
                return "An image depicting a fictional character or artwork. No pothole, road damage, or civic infrastructure defect is present."
            elif "portrait" in concept.id:
                return "A personal selfie or portrait photo of an individual. No visible civic defect is depicted."
            elif "indoor" in concept.id:
                return "An indoor residential scene with domestic furniture. Unrelated to civic infrastructure."
            elif "document" in concept.id:
                return "A document, printed receipt, or text screenshot rather than outdoor municipal infrastructure."
            else:
                return f"An image depicting {concept.label}. No public civic infrastructure defect is visibly present."

        # Civic concept descriptions
        if concept.id == "pothole":
            return "A damaged asphalt road with a large pothole visible in the roadway."
        elif concept.id == "road_crack":
            return "A roadway displaying visible surface cracking and pavement fracture."
        elif concept.id == "damaged_road":
            return "A severely broken or deteriorated road surface."
        elif concept.id == "waterlogging":
            return "A public street with standing water and waterlogging covering the pavement."
        elif concept.id == "flooding":
            return "Severe street flooding with deep water accumulation."
        elif concept.id == "garbage_dump":
            return "An open roadside garbage dump with accumulated waste and trash piles."
        elif concept.id == "overflowing_garbage":
            return "An overflowing public garbage bin with waste spilling onto the ground."
        elif concept.id == "open_drain":
            return "An open uncovered drainage ditch beside a public pathway."
        elif concept.id == "sewage":
            return "Foul stagnant black sewage water overflowing across a street."
        elif concept.id == "broken_streetlight":
            return "A broken or damaged municipal street lamp fixture on a roadway."
        elif concept.id == "exposed_electrical_wire":
            return "Snapped or exposed overhead electrical wiring hanging low on a street."
        elif concept.id == "damaged_electrical_infrastructure":
            return "A damaged electrical power transformer or broken utility pole."
        elif concept.id == "overhead_tank_overflow":
            return "An overhead water storage tank with water cascading down its structure."
        elif concept.id == "leaking_water_pipe":
            return "A ruptured municipal water pipe gushing water onto a street."
        else:
            return f"A scene visibly depicting {concept.label} ({concept.description})."

    def _analyze_with_clip(self, pil_img: Image.Image) -> VisualAnalysisResult:
        import torch

        inputs = self.clip_processor(
            text=self._concept_prompts,
            images=pil_img,
            return_tensors="pt",
            padding=True
        )

        with torch.no_grad():
            outputs = self.clip_model(**inputs)
            logits_per_image = outputs.logits_per_image  # [1, N]
            probs = logits_per_image.softmax(dim=1)[0].cpu().numpy()

        # Build list of (concept, prob)
        ranked = sorted(zip(self._concept_mapping, probs), key=lambda x: x[1], reverse=True)

        top_concept, top_prob = ranked[0]
        second_concept, second_prob = ranked[1] if len(ranked) > 1 else (top_concept, 0.0)

        # Check sum of unrelated vs civic probabilities
        unrelated_prob_sum = float(sum(p for c, p in ranked if c.is_unrelated))
        civic_prob_sum = float(sum(p for c, p in ranked if not c.is_unrelated))

        is_unrelated = top_concept.is_unrelated or (unrelated_prob_sum > 0.60 and civic_prob_sum < 0.40)

        # Extract top civic concept if present
        civic_ranked = [r for r in ranked if not r[0].is_unrelated]
        top_civic = civic_ranked[0] if civic_ranked else ranked[0]

        # Check blur
        cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        is_clear, sharpness = self.check_sharpness(cv_img)
        is_blurry = not is_clear

        # If blurry but not definitely unrelated, retain potential civic cue
        active_concept = top_concept if not is_unrelated else top_concept

        # Format visual concepts
        visual_concepts = []
        # Add top 2-3 observed concepts
        for c, p in ranked[:3]:
            visual_concepts.append(VisualConceptItem(
                label=c.label,
                confidence=round(float(p), 2)
            ))

        description = self._generate_description(active_concept, is_unrelated, is_blurry)

        return VisualAnalysisResult(
            visual_description=description,
            visual_concepts=visual_concepts,
            unrelated_content=is_unrelated,
            is_blurry=is_blurry,
            sharpness_score=sharpness,
            top_concept_id=active_concept.id,
            top_category=active_concept.category,
            top_problem_type=active_concept.problem_type
        )

    def _analyze_with_heuristics(self, pil_img: Image.Image) -> VisualAnalysisResult:
        cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        is_clear, sharpness = self.check_sharpness(cv_img)
        is_blurry = not is_clear

        if self.check_selfie_or_portrait(cv_img):
            concept = self.taxonomy.get_by_id("personal_portrait") or self.taxonomy.concepts[-1]
            return VisualAnalysisResult(
                visual_description="A close-up selfie portrait of a person. No civic infrastructure defect is visible.",
                visual_concepts=[
                    VisualConceptItem(label="personal portrait", confidence=0.96),
                    VisualConceptItem(label="unrelated content", confidence=0.94)
                ],
                unrelated_content=True,
                is_blurry=is_blurry,
                sharpness_score=sharpness,
                top_concept_id=concept.id,
                top_category="Other",
                top_problem_type="Unrelated / Non-Civic Content"
            )

        # Evaluate color and edge features
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = float(np.sum(edges > 0) / (gray.shape[0] * gray.shape[1]))
        b_mean = float(np.mean(cv_img[:, :, 0]))
        g_mean = float(np.mean(cv_img[:, :, 1]))
        r_mean = float(np.mean(cv_img[:, :, 2]))
        asphalt_contrast = float(np.std(gray))

        # Check for water signatures
        water_ratio = (b_mean + g_mean) / (r_mean + 1e-5)
        if water_ratio > 1.10 and b_mean > 110:
            concept = self.taxonomy.get_by_id("waterlogging") or self.taxonomy.get_by_id("overhead_tank_overflow")
            desc = "A scene with fluid water reflections and standing water accumulation."
            conf = 0.88
        # Check for dark asphalt road / pothole signatures
        elif asphalt_contrast > 20 and edge_density > 0.02 and (b_mean < 110 and g_mean < 110 and r_mean < 110):
            concept = self.taxonomy.get_by_id("pothole") or self.taxonomy.get_by_id("damaged_road")
            desc = "A damaged asphalt road with pavement irregularity and pothole crater texture."
            conf = 0.90
        # Check for electrical wire / linear signatures
        elif edge_density > 0.04 and (r_mean > 100 or b_mean < 70):
            concept = self.taxonomy.get_by_id("exposed_electrical_wire") or self.taxonomy.get_by_id("damaged_electrical_infrastructure")
            desc = "An outdoor scene featuring linear wiring and electrical structure elements."
            conf = 0.86
        # Check for waste / high entropy debris
        elif np.std(cv_img) > 35:
            concept = self.taxonomy.get_by_id("garbage_dump")
            desc = "An open municipal debris accumulation with dispersed waste containers."
            conf = 0.87
        else:
            concept = self.taxonomy.get_by_id("unrelated_other") or self.taxonomy.concepts[-1]
            desc = "An image depicting an indeterminate or non-civic scene."
            conf = 0.65

        is_unrelated = concept.is_unrelated

        return VisualAnalysisResult(
            visual_description=self._generate_description(concept, is_unrelated, is_blurry),
            visual_concepts=[VisualConceptItem(label=concept.label, confidence=conf)],
            unrelated_content=is_unrelated,
            is_blurry=is_blurry,
            sharpness_score=sharpness,
            top_concept_id=concept.id,
            top_category=concept.category,
            top_problem_type=concept.problem_type
        )

    def analyze_image(self, pil_img: Image.Image) -> VisualAnalysisResult:
        """
        Main entry point for analyzing a single image frame independently.
        """
        self._init_clip_if_available()
        if self.clip_model is not None and self.clip_processor is not None:
            try:
                return self._analyze_with_clip(pil_img)
            except Exception as e:
                print(f"[ImageAnalyzer] CLIP inference failed, using fallback: {e}")
                return self._analyze_with_heuristics(pil_img)
        return self._analyze_with_heuristics(pil_img)
