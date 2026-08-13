from pathlib import Path

import cv2
import numpy as np

from app.analyzers.base import AnalyzerResult

MIN_WIDTH = 320
MIN_HEIGHT = 240
MIN_ASPECT = 0.3
MAX_ASPECT = 4.0


def analyze_dimensions(image_bgr: np.ndarray, width: int, height: int) -> AnalyzerResult:
    issues: list[str] = []
    valid = True

    if width < MIN_WIDTH or height < MIN_HEIGHT:
        valid = False
        issues.append(f"Dimensions below minimum ({MIN_WIDTH}x{MIN_HEIGHT})")

    aspect = width / height if height else 0
    if aspect < MIN_ASPECT or aspect > MAX_ASPECT:
        valid = False
        issues.append(f"Unusual aspect ratio: {aspect:.2f}")

    if image_bgr is None or image_bgr.size == 0:
        valid = False
        issues.append("Image data appears corrupted or empty")

    status = "valid" if valid else "invalid"
    confidence = 0.9 if valid else 0.85

    return AnalyzerResult(
        name="dimensions",
        score=1.0 if valid else 0.0,
        status=status,
        confidence=confidence,
        details={
            "width": width,
            "height": height,
            "aspect_ratio": round(aspect, 3),
            "min_width": MIN_WIDTH,
            "min_height": MIN_HEIGHT,
        },
        issue="; ".join(issues) if issues else None,
    )


def load_image_for_analysis(file_path: Path) -> tuple[np.ndarray | None, int, int]:
    image = cv2.imread(str(file_path))
    if image is None:
        return None, 0, 0
    h, w = image.shape[:2]
    return image, w, h
