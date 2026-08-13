from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "media_pipeline",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_retry_delay=30,
    task_time_limit=300,
    task_soft_time_limit=240,
)

celery_app.autodiscover_tasks(["app.workers"])

# Ensure task module is registered
from app.workers import tasks as _tasks  # noqa: E402, F401
