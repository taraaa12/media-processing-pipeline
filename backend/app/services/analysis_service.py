from pathlib import Path

from sqlalchemy.orm import Session

from app.analyzers.aggregator import aggregate_results
from app.analyzers.blur import analyze_blur
from app.analyzers.brightness import analyze_brightness
from app.analyzers.dimensions import analyze_dimensions, load_image_for_analysis
from app.analyzers.duplicate import analyze_duplicate, compute_perceptual_hash
from app.analyzers.ocr import analyze_ocr
from app.analyzers.screenshot import analyze_screenshot
from app.analyzers.tampering import analyze_tampering
from app.core.logging import logger
from app.models.image import AnalysisResult, Image, OverallStatus


def run_full_analysis(db: Session, image: Image) -> AnalysisResult:
    file_path = Path(image.file_path)
    image_bgr, width, height = load_image_for_analysis(file_path)

    if image_bgr is None:
        raise ValueError("Failed to load image for analysis")

    # Update dimensions if missing
    if not image.width or not image.height:
        image.width = width
        image.height = height

    if not image.perceptual_hash:
        image.perceptual_hash = compute_perceptual_hash(str(file_path))

    results = [
        analyze_blur(image_bgr),
        analyze_brightness(image_bgr),
        analyze_dimensions(image_bgr, width, height),
        analyze_duplicate(db, image.sha256_hash, image.perceptual_hash, str(image.processing_id)),
        analyze_ocr(file_path),
        analyze_screenshot(image_bgr, width, height, file_path),
        analyze_tampering(image_bgr, file_path),
    ]

    aggregated = aggregate_results(results)

    blur = next(r for r in results if r.name == "blur")
    brightness = next(r for r in results if r.name == "brightness")
    duplicate = next(r for r in results if r.name == "duplicate")
    ocr = next(r for r in results if r.name == "ocr")
    dimensions = next(r for r in results if r.name == "dimensions")
    screenshot = next(r for r in results if r.name == "screenshot")
    tampering = next(r for r in results if r.name == "tampering")

    ocr_details = ocr.details or {}

    analysis = AnalysisResult(
        image_id=image.id,
        blur_score=blur.score,
        blur_status=blur.status,
        blur_confidence=blur.confidence,
        brightness_score=brightness.score,
        brightness_status=brightness.status,
        brightness_confidence=brightness.confidence,
        is_duplicate=duplicate.status in ("duplicate", "likely_duplicate"),
        duplicate_original_processing_id=(duplicate.details or {}).get("original_processing_id"),
        duplicate_confidence=duplicate.confidence if duplicate.status != "unique" else 0.0,
        duplicate_match_type=(duplicate.details or {}).get("match_type"),
        ocr_raw_text=ocr_details.get("raw_text"),
        ocr_cleaned_text=ocr_details.get("cleaned_text"),
        vehicle_number=ocr_details.get("vehicle_number"),
        vehicle_number_valid=ocr_details.get("vehicle_number_valid"),
        ocr_confidence=ocr.score,
        screenshot_probability=screenshot.score,
        screenshot_confidence=screenshot.confidence,
        screenshot_signals=(screenshot.details or {}).get("signals"),
        tampering_probability=tampering.score,
        tampering_confidence=tampering.confidence,
        tampering_signals=(tampering.details or {}).get("signals"),
        dimension_valid=dimensions.status == "valid",
        dimension_details=dimensions.details,
        overall_score=aggregated["overall_score"],
        overall_status=OverallStatus(aggregated["overall_status"]),
        overall_confidence=aggregated["overall_confidence"],
        detected_issues=aggregated["detected_issues"],
        analyzer_details=aggregated["analyzer_details"],
    )

    logger.info("Analysis completed for %s: status=%s", image.processing_id, analysis.overall_status)
    return analysis
