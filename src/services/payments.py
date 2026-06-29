from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models.payments import PaymentModel, PaymentItemModel
from src.payments.stripe import StripeService
from src.database.models.accounts import UserModel
from src.database.models.orders import (
    OrderModel,
    OrderStatusEnum,
    OrderItemModel,
)
from src.schemas.payments import (
    CheckoutResponseSchema,
)
from src.services.orders import OrderService


class PaymentService:

    @staticmethod
    def _validate_order_for_checkout(
        order: OrderModel,
    ) -> None:

        if order.status != OrderStatusEnum.PENDING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only pending orders can be paid.",
            )

        actual_amount = (
            OrderService._calculate_actual_amount(
                order,
            )
        )

        if actual_amount != order.total_amount:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Order amount has changed. "
                    "Please create a new order."
                ),
            )

    @staticmethod
    async def _get_payment_or_404(
            payment_uuid: str,
            current_user: UserModel,
            db: AsyncSession,
    ) -> PaymentModel:

        stmt = (
            select(PaymentModel)
            .options(
                selectinload(PaymentModel.items)
                .selectinload(PaymentItemModel.order_item)
                .selectinload(OrderItemModel.movie)
            )
            .where(
                PaymentModel.uuid == payment_uuid,
                PaymentModel.user_id == current_user.id,
            )
        )

        result = await db.execute(stmt)

        payment = result.scalar_one_or_none()

        if payment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found.",
            )

        return payment

    @staticmethod
    async def _get_payment_by_order(
        order_id: int,
        db: AsyncSession,
    ) -> PaymentModel | None:

        stmt = (
            select(PaymentModel)
            .where(
                PaymentModel.order_id == order_id,
            )
        )

        result = await db.execute(stmt)

        return result.scalar_one_or_none()

    @staticmethod
    async def create_checkout_session(
        order_uuid: str,
        current_user: UserModel,
        db: AsyncSession,
        stripe_service: StripeService
    ) -> CheckoutResponseSchema:

        order = await OrderService._get_order_or_404(
            order_uuid=order_uuid,
            current_user=current_user,
            db=db,
        )

        PaymentService._validate_order_for_checkout(
            order,
        )

        checkout_url = stripe_service.create_checkout_session(
            order=order,
            current_user=current_user,
        )

        return CheckoutResponseSchema(
            checkout_url=checkout_url,
        )
