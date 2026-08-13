from datetime import datetime, timezone

from app.core.logging import logger
from app.db.session import SyncSessionLocal
from app.models.image import Image, ProcessingStatus
from app.services.analysis_service import run_full_analysis
from app.workers.celery_app import celery_app


def _retry_countdown(retries: int) -> int:
    """Exponential backoff with jitter cap (mirrors Celery retry_backoff behavior)."""
    base = min(120, 2 ** retries * 10)
    return base


@celery_app.task(
    bind=True,
    name="process_image",
    max_retries=3,
)
def process_image_task(self, image_id: int) -> dict:
    db = SyncSessionLocal()
    try:
        image = db.get(Image, image_id)
        if not image:
            logger.error("Image id=%s not found for processing", image_id)
            return {"status": "not_found"}

        if image.status == ProcessingStatus.COMPLETED:
            return {"status": "already_completed"}

        image.status = ProcessingStatus.PROCESSING
        if not image.processing_start_time:
            image.processing_start_time = datetime.now(timezone.utc)
        db.commit()

        try:
            analysis = run_full_analysis(db, image)
            db.add(analysis)
            image.status = ProcessingStatus.COMPLETED
            image.processing_completion_time = datetime.now(timezone.utc)
            image.failure_reason = None
            db.commit()
            logger.info("Processing completed for image_id=%s", image_id)
            return {"status": "completed", "processing_id": str(image.processing_id)}
        except Exception as exc:
            db.rollback()
            image = db.get(Image, image_id)
            if not image:
                logger.exception("Processing failed for image_id=%s (image missing after rollback)", image_id)
                return {"status": "failed", "error": str(exc)}

            if self.request.retries < self.max_retries:
                image.status = ProcessingStatus.PROCESSING
                image.failure_reason = f"Retry {self.request.retries + 1}/{self.max_retries}: {str(exc)[:500]}"
                db.commit()
                logger.warning(
                    "Processing failed for image_id=%s, retrying (%s/%s)",
                    image_id,
                    self.request.retries + 1,
                    self.max_retries,
                )
                raise self.retry(exc=exc, countdown=_retry_countdown(self.request.retries))

            image.status = ProcessingStatus.FAILED
            image.processing_completion_time = datetime.now(timezone.utc)
            image.failure_reason = str(exc)[:2000]
            db.commit()
            logger.exception("Processing failed for image_id=%s (retries exhausted)", image_id)
            return {"status": "failed", "error": str(exc)}
    finally:
        db.close()
