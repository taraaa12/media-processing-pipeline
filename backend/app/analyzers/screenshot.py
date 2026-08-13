from pathlib import Path

import cv2
import numpy as np
from PIL import Image as PILImage
from PIL.ExifTags import TAGS

from app.analyzers.base import AnalyzerResult

COMMON_SCREEN_RATIOS = {
    16 / 9,
    9 / 16,
    4 / 3,
    3 / 4,
    19.5 / 9,
    20 / 9,
}


def _has_screen_like_ratio(width: int, height: int) -> bool:
    if not width or not height:
        return False
    ratio = width / height
    inv = height / width
    for screen_ratio in COMMON_SCREEN_RATIOS:
        if abs(ratio - screen_ratio) < 0.02 or abs(inv - screen_ratio) < 0.02:
            return True
    return False


def _detect_borders(image_bgr: np.ndarray) -> float:
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    border_width = max(3, min(h, w) // 40)
    edges = [
        gray[:border_width, :].mean(),
        gray[-border_width:, :].mean(),
        gray[:, :border_width].mean(),
        gray[:, -border_width:].mean(),
    ]
    center = gray[h // 4 : 3 * h // 4, w // 4 : 3 * w // 4].mean()
    border_avg = np.mean(edges)
    # Uniform dark/light borders suggest photo-of-screen
    border_uniformity = 1.0 - (np.std(edges) / 128.0)
    contrast = abs(border_avg - center) / 255.0
    return float(min(1.0, border_uniformity * 0.5 + contrast * 0.5))


def _detect_moire(image_bgr: np.ndarray) -> float:
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    f = np.fft.fft2(gray)
    fshift = np.fft.fftshift(f)
    magnitude = 20 * np.log(np.abs(fshift) + 1)
    h, w = magnitude.shape
    center = magnitude[h // 2 - 20 : h // 2 + 20, w // 2 - 20 : w // 2 + 20].mean()
    outer = magnitude.mean()
    ratio = outer / (center + 1e-6)
    return float(min(1.0, max(0.0, (ratio - 1.5) / 3)))


def analyze_screenshot(image_bgr: np.ndarray, width: int, height: int, file_path: Path) -> AnalyzerResult:
    signals: dict[str, float | bool | str] = {}
    probability = 0.0

    screen_ratio = _has_screen_like_ratio(width, height)
    signals["screen_like_aspect_ratio"] = screen_ratio
    if screen_ratio:
        probability += 0.25

    border_score = _detect_borders(image_bgr)
    signals["border_score"] = round(border_score, 3)
    if border_score > 0.5:
        probability += 0.25

    moire_score = _detect_moire(image_bgr)
    signals["moire_score"] = round(moire_score, 3)
    if moire_score > 0.4:
        probability += 0.2

    # Check EXIF for screenshot indicators
    try:
        with PILImage.open(file_path) as pil_img:
            exif = pil_img.getexif()
            if not exif:
                signals["missing_exif"] = True
                probability += 0.1
            else:
                exif_data = {TAGS.get(k, k): v for k, v in exif.items()}
                software = str(exif_data.get("Software", "")).lower()
                if any(s in software for s in ("screenshot", "snipping", "screen")):
                    signals["screenshot_software"] = software
                    probability += 0.35
    except Exception:
        signals["exif_read_error"] = True

    probability = min(1.0, probability)
    status = "likely_screenshot" if probability >= 0.5 else "likely_photo"
    confidence = 0.55 + probability * 0.35

    issue = None
    if probability >= 0.5:
        issue = "Image may be a screenshot or photo-of-photo (heuristic)"

    return AnalyzerResult(
        name="screenshot",
        score=probability,
        status=status,
        confidence=confidence,
        details={"signals": signals, "probability": probability},
        issue=issue,
    )
