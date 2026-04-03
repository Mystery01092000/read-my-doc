from celery import Celery

from app.config import settings

celery_app = Celery(
    "ask_my_docs",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["tasks.document_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
