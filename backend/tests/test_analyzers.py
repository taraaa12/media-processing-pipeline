import cv2
import numpy as np

from app.analyzers.aggregator import aggregate_results
from app.analyzers.base import AnalyzerResult
from app.analyzers.blur import analyze_blur
from app.analyzers.brightness import analyze_brightness
from app.models.image import OverallStatus


def test_blur_detection_sharp():
    img = np.zeros((300, 400, 3), dtype=np.uint8)
    img[50:250, 50:350] = 255
    img[100:200, 100:300] = 0
    result = analyze_blur(img)
    assert result.name == "blur"
    assert result.score is not None
    assert result.status in ("sharp", "slightly_blurry", "blurry")


def test_blur_detection_blurry():
    img = np.random.randint(100, 110, (300, 400, 3), dtype=np.uint8)
    result = analyze_blur(img)
    assert result.status in ("blurry", "slightly_blurry")


def test_brightness_dark():
    img = np.full((200, 200, 3), 15, dtype=np.uint8)
    result = analyze_brightness(img)
    assert result.status == "too_dark"
    assert result.issue is not None


def test_brightness_acceptable():
    img = np.full((200, 200, 3), 128, dtype=np.uint8)
    result = analyze_brightness(img)
    assert result.status == "acceptable"


def test_brightness_bright():
    img = np.full((200, 200, 3), 230, dtype=np.uint8)
    result = analyze_brightness(img)
    assert result.status == "too_bright"


def _agg_result(name: str, status: str, score: float = 0.5, issue: str | None = None) -> AnalyzerResult:
    return AnalyzerResult(name=name, score=score, status=status, confidence=0.8, details={}, issue=issue)


def test_aggregate_invalid_dimensions_failed():
    results = [
        _agg_result("blur", "sharp", 500),
        _agg_result("brightness", "acceptable", 128),
        _agg_result("dimensions", "invalid", issue="Invalid dimensions"),
        _agg_result("duplicate", "unique"),
        _agg_result("ocr", "success"),
        _agg_result("screenshot", "likely_photo", 0.1),
        _agg_result("tampering", "low_risk", 0.1),
    ]
    agg = aggregate_results(results)
    assert agg["overall_status"] == OverallStatus.FAILED.value
