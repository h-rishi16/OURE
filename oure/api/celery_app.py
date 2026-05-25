"""
OURE Celery Application
=======================
"""

import os

from celery import Celery

# Allow pointing to a local Redis instance or fallback to a dummy memory broker for testing
redis_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "oure_tasks", broker=redis_url, backend=redis_url, include=["oure.api.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    beat_schedule={
        "run-watchlist-screening-every-5-minutes": {
            "task": "oure.api.tasks.watchlist_screening_task",
            "schedule": 300.0,  # 5 minutes
        },
    },
)
