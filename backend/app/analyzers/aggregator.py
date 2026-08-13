from app.analyzers.base import AnalyzerResult
from app.models.image import OverallStatus


def aggregate_results(results: list[AnalyzerResult]) -> dict:
    issues: list[str] = []
    weighted_score = 0.0
    total_weight = 0.0

    weights = {
        "blur": 1.2,
        "brightness": 1.0,
        "duplicate": 1.5,
        "ocr": 0.8,
        "dimensions": 1.3,
        "screenshot": 1.1,
        "tampering": 1.2,
    }

    for result in results:
        weight = weights.get(result.name, 1.0)
        total_weight += weight

        if result.issue:
            issues.append(result.issue)

        # Convert each analyzer to a 0-1 quality score
        quality = _analyzer_quality(result)
        weighted_score += quality * weight

    overall_score = weighted_score / total_weight if total_weight else 0.5
    avg_confidence = sum(r.confidence for r in results) / len(results) if results else 0.5

    if any(r.name == "dimensions" and r.status == "invalid" for r in results):
        overall_status = OverallStatus.FAILED
    elif overall_score >= 0.75 and len(issues) <= 1:
        overall_status = OverallStatus.GOOD
    elif overall_score >= 0.5:
        overall_status = OverallStatus.NEEDS_REVIEW
    elif overall_score >= 0.25:
        overall_status = OverallStatus.POOR
    else:
        overall_status = OverallStatus.FAILED

    return {
        "overall_score": round(overall_score, 3),
        "overall_status": overall_status.value,
        "overall_confidence": round(avg_confidence, 3),
        "detected_issues": issues,
        "analyzer_details": {r.name: r.to_dict() for r in results},
    }


def _analyzer_quality(result: AnalyzerResult) -> float:
    if result.name == "blur":
        if result.status == "sharp":
            return 1.0
        if result.status == "slightly_blurry":
            return 0.7
        return 0.3
    if result.name == "brightness":
        return 1.0 if result.status == "acceptable" else 0.4
    if result.name == "duplicate":
        return 0.2 if result.status in ("duplicate", "likely_duplicate") else 1.0
    if result.name == "dimensions":
        return 1.0 if result.status == "valid" else 0.0
    if result.name == "screenshot":
        prob = result.score or 0
        return 1.0 - prob
    if result.name == "tampering":
        prob = result.score or 0
        return 1.0 - prob
    if result.name == "ocr":
        details = result.details or {}
        if details.get("vehicle_number_valid"):
            return 1.0
        if details.get("vehicle_number"):
            return 0.5
        return 0.7 if result.status == "success" else 0.6
    return 0.7
