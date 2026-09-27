import os
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "cvis_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "nightly-retention-purge": {
            "task": "app.tasks.purge_job.run_scheduled_retention_purge",
            "schedule": crontab(hour=2, minute=0), # Every night at 02:00 UTC
        },
    }
)
