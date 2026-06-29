import asyncio
from datetime import datetime, timezone

from sqlalchemy import delete

from src.celery_app import celery_app
from src.database.session import AsyncSessionLocal
from src.database.models.accounts import ActivationTokenModel, PasswordResetTokenModel


@celery_app.task
def cleanup_expired_activation_tokens():
    asyncio.run(_cleanup())


async def _cleanup():
    async with AsyncSessionLocal() as db:
        await db.execute(
            delete(ActivationTokenModel).where(
                ActivationTokenModel.expires_at <
                datetime.now(timezone.utc)
            )
        )
        await db.commit()


@celery_app.task
def cleanup_expired_password_reset_tokens():
    asyncio.run(_cleanup_reset())


async def _cleanup_reset():
    async with AsyncSessionLocal() as db:
        await db.execute(
            delete(PasswordResetTokenModel).where(
                PasswordResetTokenModel.expires_at <
                datetime.now(timezone.utc)
            )
        )
        await db.commit()
