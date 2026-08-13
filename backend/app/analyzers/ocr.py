from pathlib import Path

import cv2
import numpy as np
import pytesseract

from app.analyzers.base import AnalyzerResult
from app.utils.vehicle_number import extract_vehicle_candidates, validate_indian_vehicle_number


def analyze_ocr(file_path: Path) -> AnalyzerResult:
    try:
        image = cv2.imread(str(file_path))
        if image is None:
            return AnalyzerResult(
                name="ocr",
                status="failed",
                confidence=0.3,
                details={"error": "Could not read image for OCR"},
                issue="OCR could not read image",
            )

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Preprocess for better OCR
        gray = cv2.bilateralFilter(gray, 9, 75, 75)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        raw_text = pytesseract.image_to_string(thresh)
        cleaned = " ".join(raw_text.split())

        try:
            data = pytesseract.image_to_data(thresh, output_type=pytesseract.Output.DICT)
            confidences = [int(c) for c in data["conf"] if str(c).isdigit() and int(c) >= 0]
            ocr_confidence = float(np.mean(confidences) / 100) if confidences else 0.3
        except Exception:
            ocr_confidence = 0.3

        vehicle_number = None
        vehicle_valid = None
        vehicle_confidence = 0.0
        candidates = extract_vehicle_candidates(cleaned)
        for candidate in candidates:
            is_valid, normalized, conf = validate_indian_vehicle_number(candidate)
            if is_valid or (vehicle_number is None):
                vehicle_number = normalized
                vehicle_valid = is_valid
                vehicle_confidence = conf
            if is_valid:
                break

        issue = None
        if not cleaned:
            issue = "No text detected in image"
        elif vehicle_number and not vehicle_valid:
            issue = "Detected text but vehicle number format is invalid"

        return AnalyzerResult(
            name="ocr",
            score=ocr_confidence,
            status="success" if cleaned else "no_text",
            confidence=ocr_confidence,
            details={
                "raw_text": raw_text[:2000],
                "cleaned_text": cleaned[:2000],
                "vehicle_number": vehicle_number,
                "vehicle_number_valid": vehicle_valid,
                "vehicle_confidence": vehicle_confidence,
            },
            issue=issue,
        )
    except Exception as exc:
        return AnalyzerResult(
            name="ocr",
            status="failed",
            confidence=0.2,
            details={"error": str(exc)},
            issue="OCR processing failed (non-fatal)",
        )
