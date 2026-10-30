"""
Completeness Scorer Module for Civic Problem Intelligence (Model 1).
Evaluates report completeness across key dimensions for municipal review:
1. Location precision (GPS vs specific address vs vague vs missing)
2. Media attachment presence (photo/video available)
3. Text informativeness (word count, clarity, specificity)
4. Timestamp validity (recent/valid ISO timestamp)
Important: EXIF metadata presence/absence is explicitly NOT evaluated here (belongs exclusively to downstream Model 2).
Outputs score (0-1), list of missing fields, and constructive citizen guidance.
"""

import re
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field


class CompletenessResult(BaseModel):
    score: float
    missing_fields: List[str] = Field(default_factory=list)
    suggestions_for_citizen: List[str] = Field(default_factory=list)


# Coordinate pattern: e.g. "23.3456, 85.3421" or "(23.34, 85.34)"
GPS_REGEX = re.compile(r"[-+]?([1-8]?\d(\.\d+)?|90(\.0+)?),\s*[-+]?(180(\.0+)?|((1[0-7]\d)|([1-9]?\d))(\.\d+)?)")

# Detailed location indicators
SPECIFIC_LOC_KEYWORDS = [
    r"\bward\s*\d+\b",
    r"\bsector\s*\d+\b",
    r"\broad\b",
    r"\bchowk\b",
    r"\bcolony\b",
    r"\bmohalla\b",
    r"\bnear\b",
    r"\bopposite\b",
    r"\bgate\b",
    r"\bblock\b",
    r"\bholding\s*no\b",
    r"\bplot\s*no\b"
]

VAGUE_LOCATION_CUES = [
    r"\b(my area|my place|here|our mohalla|mera gaon|hamare yahan|near my house|near home)\b"
]


class CompletenessScorer:
    def __init__(self):
        pass

    def _evaluate_location(self, location: Optional[str]) -> tuple[float, Optional[str], Optional[str]]:
        if not location or not location.strip():
            return 0.0, "location", "Please provide the incident location or pin it on the map."

        loc_clean = location.strip()

        # 1. Exact GPS Coordinate check
        if GPS_REGEX.search(loc_clean):
            return 1.0, None, None

        # Check for vague location phrasing with little extra detail
        is_vague = any(re.search(cue, loc_clean, re.IGNORECASE) for cue in VAGUE_LOCATION_CUES)
        has_specific = any(re.search(kw, loc_clean, re.IGNORECASE) for kw in SPECIFIC_LOC_KEYWORDS)

        words = loc_clean.split()
        if len(words) < 3 and not has_specific:
            return 0.25, "precise_location", "Location is too brief. Please specify ward number, landmark, or GPS coordinates."

        if is_vague and not has_specific:
            return 0.35, "precise_location", "Location is vague. Please add the exact street, landmark, or enable GPS."

        if has_specific or len(words) >= 4:
            return 0.75, None, None

        return 0.50, "precise_location", "A more precise location (ward/colony name or GPS) will expedite officer routing."

    def _evaluate_media(self, media_count: int) -> tuple[float, Optional[str], Optional[str]]:
        if media_count <= 0:
            return 0.0, "media_attachment", "Upload a photo or short video to help verification teams assess the severity faster."
        elif media_count == 1:
            return 0.85, None, None
        else:
            return 1.0, None, None

    def _evaluate_text(self, text: Optional[str], problem_type: Optional[str] = None) -> tuple[float, Optional[str], Optional[str]]:
        if not text or not text.strip():
            return 0.0, "text_description", "Please describe the problem you are facing."

        words = text.strip().split()
        word_count = len(words)

        if word_count < 4:
            return 0.20, "detailed_description", "Description is very brief. Please explain what is happening, since when, and how it impacts people."
        elif word_count < 8:
            return 0.55, "detailed_description", "Adding more details (duration, danger level, affected area) will improve report prioritization."
        elif word_count < 15:
            return 0.85, None, None
        else:
            return 1.0, None, None

    def _evaluate_timestamp(self, timestamp: Optional[str]) -> tuple[float, Optional[str], Optional[str]]:
        if not timestamp or not str(timestamp).strip():
            return 0.0, "timestamp", "Timestamp is missing. Please provide the date and time when the issue occurred."

        try:
            ts_clean = str(timestamp).strip().replace("Z", "+00:00")
            dt = datetime.fromisoformat(ts_clean)
            now = datetime.now(timezone.utc)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)

            diff_days = (now - dt).total_seconds() / 86400
            if diff_days < -1.0:
                return 0.40, "valid_timestamp", "Timestamp appears to be in the future. Please ensure device clock is accurate."
            elif diff_days > 365:
                return 0.50, "recent_timestamp", "Reported incident date is over a year old."
            return 1.0, None, None
        except Exception:
            return 0.40, "valid_timestamp", "Timestamp format is invalid. Please supply ISO 8601 format (e.g. 2026-09-06T12:00:00Z)."

    def evaluate(
        self,
        text: Optional[str],
        media_count: int = 0,
        location: Optional[str] = None,
        timestamp: Optional[str] = None,
        problem_type: Optional[str] = None
    ) -> CompletenessResult:
        missing_fields: List[str] = []
        suggestions: List[str] = []

        loc_score, loc_missing, loc_sugg = self._evaluate_location(location)
        if loc_missing:
            missing_fields.append(loc_missing)
        if loc_sugg:
            suggestions.append(loc_sugg)

        media_score, media_missing, media_sugg = self._evaluate_media(media_count)
        if media_missing:
            missing_fields.append(media_missing)
        if media_sugg:
            suggestions.append(media_sugg)

        text_score, text_missing, text_sugg = self._evaluate_text(text, problem_type=problem_type)
        if text_missing:
            missing_fields.append(text_missing)
        if text_sugg:
            suggestions.append(text_sugg)

        time_score, time_missing, time_sugg = self._evaluate_timestamp(timestamp)
        if time_missing:
            missing_fields.append(time_missing)
        if time_sugg:
            suggestions.append(time_sugg)

        # Weighted total (Weights: Location=0.35, Media=0.30, Text=0.25, Timestamp=0.10)
        weighted_total = (
            (loc_score * 0.35) +
            (media_score * 0.30) +
            (text_score * 0.25) +
            (time_score * 0.10)
        )

        return CompletenessResult(
            score=round(float(weighted_total), 2),
            missing_fields=missing_fields,
            suggestions_for_citizen=suggestions
        )
