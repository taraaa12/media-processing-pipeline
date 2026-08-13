import cv2
import numpy as np

from app.analyzers.base import AnalyzerResult


def analyze_brightness(image_bgr: np.ndarray) -> AnalyzerResult:
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    mean_brightness = float(np.mean(gray))
    score = mean_brightness

    if mean_brightness < 50:
        status = "too_dark"
        confidence = min(0.9, 0.6 + (50 - mean_brightness) / 80)
        issue = "Image is too dark / low light"
    elif mean_brightness > 200:
        status = "too_bright"
        confidence = min(0.9, 0.6 + (mean_brightness - 200) / 55)
        issue = "Image is overexposed / too bright"
    else:
        status = "acceptable"
        confidence = 0.75
        issue = None

    return AnalyzerResult(
        name="brightness",
        score=score,
        status=status,
        confidence=confidence,
        details={"mean_brightness": mean_brightness},
        issue=issue,
    )
