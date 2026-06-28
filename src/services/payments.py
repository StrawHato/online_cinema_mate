from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.payments.stripe import StripeService
from src.database.models.accounts import UserModel
from src.database.models.orders import (
    OrderModel,
    OrderStatusEnum,
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

        checkout_url = await stripe_service.create_checkout_session(
            order=order,
            current_user=current_user,
        )

        return CheckoutResponseSchema(
            checkout_url=checkout_url,
        )
