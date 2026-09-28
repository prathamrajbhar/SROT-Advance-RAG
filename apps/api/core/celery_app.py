from celery import Celery
from kombu import Queue
from core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "srot_workers",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["modules.documents.tasks"],
)

celery_app.conf.update(
    imports=["modules.documents.tasks"],
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    worker_prefetch_multiplier=1,
    task_queues=[
        Queue("celery-docs", routing_key="docs.#"),
        Queue("celery-media", routing_key="media.#"),
        Queue("celery-default", routing_key="default.#"),
    ],
    task_routes={
        "modules.documents.tasks.process_document_task": {"queue": "celery-docs"},
        "modules.documents.tasks.process_media_task": {"queue": "celery-media"},
        "modules.documents.tasks.*": {"queue": "celery-default"},
    },
)
