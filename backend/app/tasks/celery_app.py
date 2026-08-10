from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "clinical_qc",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.worker"],
)
celery_app.conf.task_track_started = True
celery_app.conf.worker_prefetch_multiplier = 1

