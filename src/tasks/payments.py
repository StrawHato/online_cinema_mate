import asyncio

import aiosmtplib
from celery import shared_task

from src.config.dependencies import (
    get_accounts_email_notificator,
)
from src.database.models.orders import OrderItemModel
from src.database.models.payments import (
    PaymentItemModel,
    PaymentModel,
)
from src.database.session import AsyncSessionLocal
from sqlalchemy import select
from sqlalchemy.orm import selectinload


@shared_task(
    autoretry_for=(
        aiosmtplib.SMTPException,
        ConnectionError,
    ),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def send_payment_success_email_task(
    payment_id: int,
):
    asyncio.run(
        _send_payment_success_email(
            payment_id,
        )
    )


async def _send_payment_success_email(
    payment_id: int,
) -> None:

    async with AsyncSessionLocal() as db:

        stmt = (
            select(PaymentModel)
            .options(
                selectinload(PaymentModel.user),
                selectinload(PaymentModel.items)
                .selectinload(PaymentItemModel.order_item)
                .selectinload(OrderItemModel.movie),
            )
            .where(
                PaymentModel.id == payment_id,
            )
        )

        result = await db.execute(stmt)

        payment = result.scalar_one_or_none()

        if payment is None:
            return

        sender = get_accounts_email_notificator()

        await sender.send_payment_success_email(
            email=payment.user.email,
            payment_uuid=payment.uuid,
            amount=payment.amount,
            payment_date=payment.created_at,
            movies=[
                item.order_item.movie.name
                for item in payment.items
            ],
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
def send_payment_refunded_email_task(
    payment_id: int,
):
    asyncio.run(
        _send_payment_refunded_email(
            payment_id,
        )
    )


async def _send_payment_refunded_email(
    payment_id: int,
) -> None:

    async with AsyncSessionLocal() as db:
        stmt = (
            select(PaymentModel)
            .options(
                selectinload(PaymentModel.user),
                selectinload(PaymentModel.items)
                .selectinload(PaymentItemModel.order_item)
                .selectinload(OrderItemModel.movie),
            )
            .where(
                PaymentModel.id == payment_id,
            )
        )

        result = await db.execute(stmt)

        payment = result.scalar_one_or_none()

        if payment is None:
            return

        sender = get_accounts_email_notificator()

        await sender.send_payment_refunded_email(
            email=payment.user.email,
            payment_uuid=payment.uuid,
            amount=payment.amount,
            refund_date=payment.created_at,
            movies=[
                item.order_item.movie.name
                for item in payment.items
            ],
        )
