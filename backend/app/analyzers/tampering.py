from pathlib import Path

import cv2
import numpy as np
from PIL import Image as PILImage
from PIL.ExifTags import TAGS

from app.analyzers.base import AnalyzerResult

EDITING_SOFTWARE_KEYWORDS = (
    "photoshop", "gimp", "lightroom", "snapseed", "picsart", "canva", "paint",
    "affinity", "pixelmator", "fotor",
)


def _check_exif_editing(file_path: Path) -> tuple[float, dict]:
    signals: dict = {}
    score = 0.0
    try:
        with PILImage.open(file_path) as img:
            exif = img.getexif()
            if not exif:
                signals["no_exif"] = True
                score += 0.15
            else:
                exif_data = {TAGS.get(k, k): v for k, v in exif.items()}
                software = str(exif_data.get("Software", "")).lower()
                if software:
                    signals["software"] = software
                    if any(kw in software for kw in EDITING_SOFTWARE_KEYWORDS):
                        score += 0.4
                        signals["editing_software_detected"] = True
                # Missing camera make/model on field photos can be suspicious
                if not exif_data.get("Make") and not exif_data.get("Model"):
                    signals["missing_camera_info"] = True
                    score += 0.1
    except Exception as exc:
        signals["exif_error"] = str(exc)
    return score, signals


def _check_recompression_artifacts(image_bgr: np.ndarray) -> tuple[float, dict]:
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    noise = float(np.std(laplacian))
    # Very low or very high noise can indicate recompression
    artifact_score = 0.0
    if noise < 5:
        artifact_score = 0.2
    elif noise > 80:
        artifact_score = 0.15
    return artifact_score, {"laplacian_noise_std": round(noise, 3)}


def _check_inconsistent_regions(image_bgr: np.ndarray) -> tuple[float, dict]:
    h, w = image_bgr.shape[:2]
    if h < 100 or w < 100:
        return 0.0, {}
    regions = []
    for y in range(0, h, h // 3):
        for x in range(0, w, w // 3):
            patch = image_bgr[y : y + h // 3, x : x + w // 3]
            if patch.size == 0:
                continue
            regions.append(float(np.std(patch)))
    if len(regions) < 2:
        return 0.0, {}
    variation = float(np.std(regions) / (np.mean(regions) + 1e-6))
    score = min(0.3, variation * 0.5) if variation > 0.8 else 0.0
    return score, {"region_std_variation": round(variation, 3)}


def analyze_tampering(image_bgr: np.ndarray, file_path: Path) -> AnalyzerResult:
    signals: dict = {}
    probability = 0.0

    exif_score, exif_signals = _check_exif_editing(file_path)
    probability += exif_score
    signals.update(exif_signals)

    artifact_score, artifact_signals = _check_recompression_artifacts(image_bgr)
    probability += artifact_score
    signals.update(artifact_signals)

    region_score, region_signals = _check_inconsistent_regions(image_bgr)
    probability += region_score
    signals.update(region_signals)

    probability = min(1.0, probability)
    status = "suspicious" if probability >= 0.45 else "normal"
    confidence = 0.5 + min(0.4, probability)

    issue = None
    if probability >= 0.45:
        issue = "Possible editing/tampering indicators detected (heuristic, not forensic)"

    return AnalyzerResult(
        name="tampering",
        score=probability,
        status=status,
        confidence=confidence,
        details={"signals": signals, "probability": probability},
        issue=issue,
    )
