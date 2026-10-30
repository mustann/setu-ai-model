"""
Severity Scorer Module for Civic Problem Intelligence (Model 1).
Extracts severity signals (temporal cues, hazard cues, vulnerability cues, scale cues)
and computes a calibrated categorical severity level ('Low', 'Medium', 'High', 'Critical')
with a confidence score, a list of detected signals, and an explainable reason.
"""

import re
from typing import List, Dict, Tuple, Optional
from pydantic import BaseModel, Field


class SeverityResult(BaseModel):
    level: str  # "Low" | "Medium" | "High" | "Critical"
    confidence: float
    signals: List[str] = Field(default_factory=list)
    reason: str = ""


# Pattern definitions with signal weights
HAZARD_SIGNALS = [
    (r"\b(spark|sparking|sparks|short circuit|live wire|bare wire|11kv|high-tension|electric shock|current lag)\b", "High-risk electrical hazard detected", 4.5),
    (r"\b(blast|explosion|burst|caught fire|catching fire|burning|toxic smoke)\b", "Fire/explosion or toxic hazard detected", 4.5),
    (r"\b(collapse|collapsed|sinkhole|crater|culvert collapsed|bridge broken|death trap|lethal|fatal)\b", "Severe structural hazard or deadly road failure", 4.5),
    (r"\b(medical waste|hospital waste|bio-waste|dengue outbreak|cholera|epidemic|poisonous)\b", "Severe public health bio-hazard", 4.0),
    (r"\b(falling down|slipping and falling|accidents?|injury|injured|bleeding)\b", "Direct physical accidents or injuries occurring", 3.0),
    (r"\b(entering houses?|flooding into homes?|backing up into houses?)\b", "Sewage/water inundating residential living spaces", 3.5),
]

VULNERABILITY_SIGNALS = [
    (r"\b(children|kids|bachh?e|students|primary school|school gate|anganwadi|nursery)\b", "Vulnerable children or school environment at risk", 2.5),
    (r"\b(hospital|patients|ambulance|rims|clinic|emergency)\b", "Healthcare access or medical patients impacted", 3.0),
    (r"\b(elderly|senior citizens?|disabled)\b", "Vulnerable elderly or disabled persons impacted", 2.0),
]

WORD_TO_NUM = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "several": 4, "multiple": 3
}

TEMPORAL_PATTERNS = [
    (r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|several|multiple)\s*(days?|din)\b", 1),       # captures 'X days'
    (r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|several|multiple)\s*(weeks?|haf?te)\b", 2),   # captures 'X weeks'
    (r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|several|multiple)\s*(months?|mahine)\b", 3),  # captures 'X months'
    (r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|several|multiple)\s*(hours?|ghante)\b", 0),   # captures 'X hours'
]

SCALE_SIGNALS = [
    (r"\b(entire colony|entire village|entire neighborhood|all houses|whole street|hundreds of families|whole colony)\b", "Large-scale community impact", 2.5),
    (r"\b(no water supply|no water for|no drinking water|complete water outage|no supply for|outage for|water crisis|complete darkness|blackout for)\b", "Severe prolonged deprivation of essential civic utility", 3.0),
    (r"\b(traffic halted|road blocked|completely cut off|impassable|large obstruction)\b", "Critical transportation artery blocked", 2.5),
]

LOW_SEVERITY_CUES = [
    r"\b(minor|small issue|slight|slow leak|slowly|single bulb|faded|prune|cosmetic|whenever possible|non-urgent)\b"
]


class SeverityScorer:
    def __init__(self):
        pass

    def evaluate(self, text: str, domain: Optional[str] = None) -> SeverityResult:
        if not text or not text.strip():
            return SeverityResult(
                level="Low",
                confidence=0.50,
                signals=["No complaint details provided"],
                reason="Default baseline severity assigned due to lack of descriptive signals."
            )

        text_lower = text.lower()
        extracted_signals: List[str] = []
        total_score = 0.0

        # 1. Check Hazard Signals
        for pattern, label, weight in HAZARD_SIGNALS:
            match = re.search(pattern, text_lower)
            if match:
                extracted_signals.append(f"{label} ('{match.group(0)}')")
                total_score += weight

        # 2. Check Vulnerability Signals
        for pattern, label, weight in VULNERABILITY_SIGNALS:
            match = re.search(pattern, text_lower)
            if match:
                extracted_signals.append(f"{label} ('{match.group(0)}')")
                total_score += weight

        # 3. Check Temporal Signals (duration of issue)
        for pattern, time_scale in TEMPORAL_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                raw_qty = match.group(1).lower()
                qty = int(raw_qty) if raw_qty.isdigit() else WORD_TO_NUM.get(raw_qty, 3)
                unit = match.group(2)
                if time_scale == 0:  # hours
                    if qty >= 12:
                        total_score += 2.0
                        extracted_signals.append(f"Ongoing duration: {qty} {unit}")
                elif time_scale == 1:  # days
                    if qty >= 3:
                        total_score += 3.0
                        extracted_signals.append(f"Persistent duration: {qty} {unit}")
                    elif qty >= 1:
                        total_score += 1.5
                        extracted_signals.append(f"Duration: {qty} {unit}")
                elif time_scale >= 2:  # weeks or months
                    total_score += 3.5
                    extracted_signals.append(f"Chronic duration: {qty} {unit}")

        # 4. Check Scale Signals
        for pattern, label, weight in SCALE_SIGNALS:
            match = re.search(pattern, text_lower)
            if match:
                extracted_signals.append(label)
                total_score += weight

        # 5. Check Low Severity Dampeners
        for pattern in LOW_SEVERITY_CUES:
            match = re.search(pattern, text_lower)
            if match:
                total_score -= 2.0
                extracted_signals.append(f"Low urgency indicator ('{match.group(0)}')")

        # Domain-specific baseline adjustment
        if domain and "electr" in domain.lower() and any(k in text_lower for k in ["spark", "wire", "shock", "fire"]):
            total_score += 1.0
        elif domain and "water" in domain.lower() and any(k in text_lower for k in ["overflow", "flooding", "no water"]):
            total_score += 1.0

        # Categorization logic
        if total_score >= 6.0:
            level = "Critical"
            confidence = min(0.98, 0.78 + (total_score - 6.0) * 0.04)
            reason = "Critical danger identified: imminent life safety or widespread hazardous failure."
        elif total_score >= 3.5:
            level = "High"
            confidence = min(0.94, 0.72 + (total_score - 3.5) * 0.06)
            reason = "High severity: significant public impact, prolonged outage, or active hazard."
        elif total_score >= 1.5:
            level = "Medium"
            confidence = min(0.88, 0.65 + (total_score - 1.5) * 0.08)
            reason = "Moderate disruption requiring scheduled municipal resolution."
        else:
            level = "Low"
            confidence = max(0.60, 0.85 - (total_score * 0.1))
            reason = "Minor civic grievance or cosmetic defect with minimal immediate hazard."

        if not extracted_signals:
            extracted_signals.append("Standard civic grievance; no emergency keywords detected")

        return SeverityResult(
            level=level,
            confidence=round(float(confidence), 4),
            signals=extracted_signals,
            reason=reason
        )
