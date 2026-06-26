"""
RES - cost_estimator/photo_handler.py
=====================================
Photo intake helpers for the cost estimator.
"""

from pathlib import Path
from shutil import copy2
from uuid import uuid4

from config import AppConfig


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def store_uploaded_photo(source_path: str | Path) -> Path:
    """
    Copy a user-provided photo into managed estimator storage.

    Args:
        source_path: Existing image path.

    Returns:
        Destination path under PHOTO_STORAGE_PATH/cost_estimator.
    """
    source = Path(source_path)
    if not source.exists() or not source.is_file():
        raise ValueError(f"Photo does not exist: {source}")
    if source.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError("Unsupported photo type. Use JPG, PNG, or WEBP.")

    target_dir = AppConfig.PHOTO_STORAGE_PATH / "cost_estimator"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{uuid4().hex}{source.suffix.lower()}"
    copy2(source, target)
    return target
