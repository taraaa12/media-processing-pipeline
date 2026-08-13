import imagehash
from PIL import Image as PILImage
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analyzers.base import AnalyzerResult
from app.models.image import Image, ProcessingStatus


def compute_perceptual_hash(file_path: str) -> str:
    with PILImage.open(file_path) as img:
        return str(imagehash.phash(img))


def analyze_duplicate(
    db: Session,
    sha256_hash: str,
    perceptual_hash: str | None,
    current_processing_id: str,
) -> AnalyzerResult:
    # Exact duplicate via SHA-256
    exact_stmt = (
        select(Image)
        .where(Image.sha256_hash == sha256_hash)
        .where(Image.processing_id != current_processing_id)
        .where(Image.status == ProcessingStatus.COMPLETED)
        .order_by(Image.upload_time.asc())
        .limit(1)
    )
    exact_match = db.execute(exact_stmt).scalar_one_or_none()

    if exact_match:
        return AnalyzerResult(
            name="duplicate",
            score=1.0,
            status="duplicate",
            confidence=0.99,
            details={
                "match_type": "exact_sha256",
                "original_processing_id": str(exact_match.processing_id),
            },
            issue="Exact duplicate of a previously uploaded image",
        )

    # Perceptual hash - check hamming distance
    if perceptual_hash:
        all_images = db.execute(
            select(Image)
            .where(Image.perceptual_hash.isnot(None))
            .where(Image.processing_id != current_processing_id)
            .where(Image.status == ProcessingStatus.COMPLETED)
        ).scalars().all()

        current_hash = imagehash.hex_to_hash(perceptual_hash)
        for img in all_images:
            if not img.perceptual_hash:
                continue
            try:
                other_hash = imagehash.hex_to_hash(img.perceptual_hash)
                distance = current_hash - other_hash
                if distance <= 5:
                    confidence = max(0.6, 0.95 - distance * 0.07)
                    return AnalyzerResult(
                        name="duplicate",
                        score=float(distance),
                        status="likely_duplicate",
                        confidence=confidence,
                        details={
                            "match_type": "perceptual_hash",
                            "hamming_distance": distance,
                            "original_processing_id": str(img.processing_id),
                        },
                        issue="Image appears visually similar to a previous upload",
                    )
            except Exception:
                continue

    return AnalyzerResult(
        name="duplicate",
        score=0.0,
        status="unique",
        confidence=0.8,
        details={"match_type": None},
        issue=None,
    )
