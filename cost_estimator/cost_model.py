"""
RES - cost_estimator/cost_model.py
==================================
Cost range model for estimator severity outputs.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class CostEstimate:
    """Estimated repair cost output."""

    severity: str
    low: float
    high: float
    recommended: float
    confidence: float
    rationale: str


RANGES = {
    "LOW": (100.0, 500.0),
    "MEDIUM": (500.0, 1800.0),
    "HIGH": (1800.0, 6500.0),
}


def estimate_cost(severity: str, confidence: float, rationale: str = "") -> CostEstimate:
    """
    Convert severity into a cost range.

    Args:
        severity: LOW, MEDIUM, or HIGH.
        confidence: Classification confidence.
        rationale: Explanation carried forward from the classifier.

    Returns:
        CostEstimate.
    """
    normalized = severity.upper()
    if normalized not in RANGES:
        raise ValueError(f"Unsupported severity: {severity}")
    low, high = RANGES[normalized]
    recommended = low + ((high - low) * 0.55)
    return CostEstimate(
        severity=normalized,
        low=low,
        high=high,
        recommended=recommended,
        confidence=confidence,
        rationale=rationale,
    )
