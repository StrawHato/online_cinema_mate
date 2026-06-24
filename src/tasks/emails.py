import asyncio

import aiosmtplib
from celery import shared_task
from src.config.dependencies import (
    get_accounts_email_notificator
)


@shared_task(
    autoretry_for=(
        aiosmtplib.SMTPException,
        ConnectionError,
    ),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def send_activation_email_task(
    email: str,
    activation_link: str,
):
    sender = get_accounts_email_notificator()

    asyncio.run(
        sender.send_activation_email(
            email,
            activation_link,
        )
    )


@shared_task(
    autoretry_for=(
        aiosmtplib.SMTPException,
        ConnectionError,
    ),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def send_activation_complete_email_task(
    email: str,
    login_link: str,
) -> None:
    sender = get_accounts_email_notificator()

    asyncio.run(
        sender.send_activation_complete_email(
            email=email,
            login_link=login_link,
        )
    )

@shared_task(
    autoretry_for=(
        aiosmtplib.SMTPException,
        ConnectionError,
    ),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def send_password_reset_email_task(
    email: str,
    reset_link: str,
) -> None:
    sender = get_accounts_email_notificator()

    asyncio.run(
        sender.send_password_reset_email(
            email=email,
            reset_link=reset_link,
        )
    )


@shared_task(
    autoretry_for=(
        aiosmtplib.SMTPException,
        ConnectionError,
    ),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def send_password_reset_complete_email_task(
    email: str,
    login_link: str,
) -> None:
    sender = get_accounts_email_notificator()

    asyncio.run(
        sender.send_password_reset_complete_email(
            email=email,
            login_link=login_link,
        )
    )
