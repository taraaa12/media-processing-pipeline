import cv2
import numpy as np

from app.analyzers.base import AnalyzerResult


def analyze_blur(image_bgr: np.ndarray) -> AnalyzerResult:
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    score = float(laplacian_var)

    # Heuristic thresholds - variance of Laplacian
    if score < 50:
        status = "blurry"
        confidence = min(0.95, 0.6 + (50 - score) / 100)
        issue = "Image appears blurry (low edge detail)"
    elif score < 100:
        status = "slightly_blurry"
        confidence = 0.65
        issue = "Image may be slightly out of focus"
    else:
        status = "sharp"
        confidence = min(0.9, 0.5 + score / 500)
        issue = None

    return AnalyzerResult(
        name="blur",
        score=score,
        status=status,
        confidence=confidence,
        details={"laplacian_variance": score, "method": "variance_of_laplacian"},
        issue=issue,
    )
