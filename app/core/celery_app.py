from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "url_shortener",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Celery Beat schedule configuration
celery_app.conf.beat_schedule = {
    "aggregate-clicks-every-hour": {
        "task": "app.tasks.analytics.aggregate_clicks_task",
        "schedule": 3600.0,  # Every hour (in seconds)
    }
}

# Auto-discover tasks in app package
celery_app.autodiscover_tasks(["app"])
