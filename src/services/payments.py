from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from stripe.checkout import Session

from src.database.models.payments import (
    PaymentModel,
    PaymentItemModel,
    PaymentStatusEnum
)
from src.payments.stripe import StripeService
from src.database.models.accounts import UserModel
from src.database.models.orders import (
    OrderModel,
    OrderStatusEnum,
    OrderItemModel,
)
from src.schemas.payments import (
    CheckoutResponseSchema,
    PaymentResponseSchema,
    PaymentItemResponseSchema,
)
from src.schemas.orders import OrderMovieResponseSchema
from src.services.orders import OrderService
from src.tasks.payments import send_payment_success_email


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
    def _to_payment_response(
        payment: PaymentModel,
    ) -> PaymentResponseSchema:

        return PaymentResponseSchema(
            uuid=payment.uuid,
            created_at=payment.created_at,
            status=payment.status,
            amount=payment.amount,
            items=[
                PaymentItemResponseSchema(
                    id=item.id,
                    price_at_payment=item.price_at_payment,
                    movie=OrderMovieResponseSchema(
                        uuid=item.order_item.movie.uuid,
                        name=item.order_item.movie.name,
                        year=item.order_item.movie.year,
                    ),
                )
                for item in payment.items
            ],
        )

    @staticmethod
    async def _get_payment_or_none_by_external_id(
        external_payment_id: str,
        db: AsyncSession,
    ) -> PaymentModel | None:

        stmt = (
            select(PaymentModel)
            .where(
                PaymentModel.external_payment_id == external_payment_id,
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

    @staticmethod
    async def process_webhook(
            payload: bytes,
            signature: str,
            stripe_service: StripeService,
            db: AsyncSession,
    ) -> None:

        event = stripe_service.verify_webhook(
            payload=payload,
            signature=signature,
        )

        if event["type"] != "checkout.session.completed":
            return

        session: Session = event["data"]["object"]

        metadata = session.metadata

        if metadata is None:
            return

        try:
            order_uuid = metadata["order_uuid"]
        except KeyError:
            return

        if order_uuid is None:
            return

        stmt = (
            select(OrderModel)
            .options(
                selectinload(OrderModel.items)
                .selectinload(OrderItemModel.movie)
            )
            .where(
                OrderModel.uuid == order_uuid,
            )
        )

        result = await db.execute(stmt)

        order = result.scalar_one_or_none()

        if order is None:
            return

        if order.status == OrderStatusEnum.PAID:
            return

        existing_payment = (
            await PaymentService._get_payment_by_order(
                order_id=order.id,
                db=db,
            )
        )

        if existing_payment is not None:
            return

        payment = PaymentModel(
            user_id=order.user_id,
            order_id=order.id,
            amount=order.total_amount,
            status=PaymentStatusEnum.SUCCESSFUL,
            external_payment_id=session.payment_intent,
        )

        db.add(payment)

        await db.flush()

        for order_item in order.items:
            payment_item = PaymentItemModel(
                payment_id=payment.id,
                order_item_id=order_item.id,
                price_at_payment=order_item.price_at_order,
            )

            db.add(payment_item)

        order.status = OrderStatusEnum.PAID

        await db.commit()

        send_payment_success_email.delay(
            payment.id,
        )

    @staticmethod
    async def get_payment(
            payment_uuid: str,
            current_user: UserModel,
            db: AsyncSession,
    ) -> PaymentResponseSchema:

        payment = await PaymentService._get_payment_or_404(
            payment_uuid=payment_uuid,
            current_user=current_user,
            db=db,
        )

        return PaymentService._to_payment_response(
            payment,
        )
