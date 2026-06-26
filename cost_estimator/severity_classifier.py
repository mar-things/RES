"""
RES - cost_estimator/severity_classifier.py
===========================================
Severity classification for vehicle damage estimates.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SeverityResult:
    """Damage severity classification output."""

    severity: str
    confidence: float
    rationale: str


def classify_from_description(description: str) -> SeverityResult:
    """
    Classify damage severity using deterministic keyword rules.

    Args:
        description: Damage description or AI-generated caption.

    Returns:
        SeverityResult with LOW, MEDIUM, or HIGH.
    """
    text = description.lower()
    high_terms = {"frame", "airbag", "structural", "chassis", "engine", "suspension"}
    medium_terms = {"bumper", "door", "fender", "paint", "dent", "panel", "headlight"}
    if any(term in text for term in high_terms):
        return SeverityResult("HIGH", 0.78, "Structural or safety-critical terms detected.")
    if any(term in text for term in medium_terms):
        return SeverityResult("MEDIUM", 0.70, "Body-panel or paint repair terms detected.")
    return SeverityResult("LOW", 0.60, "No high-impact damage terms detected.")
