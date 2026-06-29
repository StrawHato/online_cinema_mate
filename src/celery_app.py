from celery import Celery
from celery.schedules import crontab

from src.config.settings import get_settings


settings = get_settings()

celery_app = Celery(
    "online_cinema",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

import src.tasks.accounts
import src.tasks.emails
import src.tasks.payments

celery_app.conf.timezone = "UTC"

celery_app.conf.beat_schedule = {
    "cleanup-expired-activation-tokens": {
        "task": (
            "src.tasks.accounts."
            "cleanup_expired_activation_tokens"
        ),
        "schedule": crontab(hour="*/1"),
    },
    "cleanup-expired-password-reset-tokens": {
        "task": (
            "src.tasks.accounts."
            "cleanup_expired_password_reset_tokens"
        ),
        "schedule": crontab(hour="*/1"),
    },
}
