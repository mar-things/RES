"""
RES - cost_estimator/ai_engine.py
=================================
OpenAI Vision integration with offline fallback.
"""

from pathlib import Path

from config import AppConfig
from cost_estimator.cost_model import CostEstimate, estimate_cost
from cost_estimator.photo_handler import store_uploaded_photo
from cost_estimator.severity_classifier import classify_from_description


def estimate_from_photo(photo_path: str | Path, description: str = "") -> tuple[Path, CostEstimate]:
    """
    Estimate damage cost from a photo and optional description.

    The current MVP uses deterministic fallback unless OpenAI integration is
    explicitly configured. This keeps workshop usage offline-safe.

    Args:
        photo_path: Source image path.
        description: Optional operator description.

    Returns:
        Tuple of stored photo path and cost estimate.
    """
    stored = store_uploaded_photo(photo_path)
    analysis_text = description.strip()
    if AppConfig.OPENAI_API_KEY:
        analysis_text = _openai_caption(stored, analysis_text)
    result = classify_from_description(analysis_text or stored.name)
    return stored, estimate_cost(result.severity, result.confidence, result.rationale)


def _openai_caption(photo_path: Path, description: str) -> str:
    """
    Return an OpenAI-generated damage caption when the SDK is installed.

    Args:
        photo_path: Stored photo path.
        description: Operator-provided context.

    Returns:
        Caption text, or the original description on integration failure.
    """
    try:
        from openai import OpenAI

        client = OpenAI(api_key=AppConfig.OPENAI_API_KEY)
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "Describe visible vehicle damage for repair cost "
                                f"estimation. Operator note: {description or 'none'}"
                            ),
                        },
                        {
                            "type": "input_image",
                            "image_url": photo_path.resolve().as_uri(),
                        },
                    ],
                }
            ],
        )
        return response.output_text or description
    except Exception as exc:
        print(f"[CostEstimator] OpenAI analysis unavailable: {exc}")
        return description
