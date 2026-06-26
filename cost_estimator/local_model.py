"""
RES - cost_estimator/local_model.py
===================================
Interface for future local YOLOv8/IP-camera estimation.
"""

from pathlib import Path

from cost_estimator.severity_classifier import SeverityResult, classify_from_description


class LocalDamageModel:
    """
    Local model adapter boundary.

    A future YOLOv8 implementation can load weights in this class and return
    the same SeverityResult contract used by the estimator pipeline.
    """

    def __init__(self, weights_path: str | Path | None = None) -> None:
        """
        Initialize the local adapter.

        Args:
            weights_path: Optional local model weights path.
        """
        self.weights_path = Path(weights_path) if weights_path else None

    def classify_image(self, image_path: str | Path, hint: str = "") -> SeverityResult:
        """
        Classify a local image.

        Args:
            image_path: Image path from smartphone upload or IP camera capture.
            hint: Optional operator context.

        Returns:
            SeverityResult compatible with the cost model.
        """
        image = Path(image_path)
        if not image.exists():
            raise ValueError(f"Image does not exist: {image}")
        return classify_from_description(hint or image.stem)
