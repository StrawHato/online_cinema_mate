from celery import shared_task
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.database.models.orders import OrderItemModel
from src.database.models.payments import (
    PaymentModel,
    PaymentItemModel,
)
from src.database.session import AsyncSessionLocal
from src.notifications.emails import EmailSender


@shared_task
async def send_payment_success_email(
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

        movies = [
            item.order_item.movie.name
            for item in payment.items
        ]

        await EmailSender.send_payment_success_email(
            recipient=payment.user.email,
            amount=payment.amount,
            payment_date=payment.created_at,
            movies=movies,
        )
