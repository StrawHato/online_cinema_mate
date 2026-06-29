from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select, func
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
    PaymentListResponseSchema,
)
from src.schemas.orders import OrderMovieResponseSchema
from src.services.orders import OrderService
from src.tasks.payments import (
    send_payment_success_email_task,
    send_payment_refunded_email_task
)


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
                selectinload(PaymentModel.order),
                selectinload(PaymentModel.items)
                .selectinload(PaymentItemModel.order_item)
                .selectinload(OrderItemModel.movie),
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

        existing_payment = await PaymentService._get_payment_by_order(
            order_id=order.id,
            db=db,
        )

        if existing_payment is not None:

            if existing_payment.status == PaymentStatusEnum.SUCCESSFUL:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Payment has already been completed.",
                )

            if existing_payment.status == PaymentStatusEnum.REFUNDED:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Refunded payments cannot be reused.",
                )

            payment = existing_payment

            payment.status = PaymentStatusEnum.PENDING
            payment.external_payment_id = None

        else:
            payment = PaymentModel(
                user_id=current_user.id,
                order_id=order.id,
                amount=order.total_amount,
                status=PaymentStatusEnum.PENDING,
            )

            db.add(payment)

        await db.flush()
        await db.commit()
        await db.refresh(payment)

        checkout_url = stripe_service.create_checkout_session(
            order=order,
            payment=payment,
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
            payment_uuid = metadata["payment_uuid"]
        except KeyError:
            return

        if payment_uuid is None:
            return

        stmt = (
            select(PaymentModel)
            .options(
                selectinload(PaymentModel.order)
                .selectinload(OrderModel.items)
                .selectinload(OrderItemModel.movie),

                selectinload(PaymentModel.items),
            )
            .where(
                PaymentModel.uuid == payment_uuid,
            )
        )

        result = await db.execute(stmt)

        payment = result.scalar_one_or_none()

        if payment is None:
            return

        order = payment.order

        if payment.status == PaymentStatusEnum.SUCCESSFUL:
            return

        if order is None:
            return

        if order.status == OrderStatusEnum.PAID:
            return

        payment.status = PaymentStatusEnum.SUCCESSFUL
        payment.external_payment_id = session.payment_intent

        for order_item in order.items:
            payment_item = PaymentItemModel(
                payment_id=payment.id,
                order_item_id=order_item.id,
                price_at_payment=order_item.price_at_order,
            )

            db.add(payment_item)

        order.status = OrderStatusEnum.PAID

        await db.commit()

        send_payment_success_email_task.delay(
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

    @staticmethod
    async def get_payments(
            current_user: UserModel,
            db: AsyncSession,
            page: int,
            page_size: int,
    ) -> PaymentListResponseSchema:

        count_stmt = (
            select(func.count(PaymentModel.id))
            .where(
                PaymentModel.user_id == current_user.id,
            )
        )

        total = await db.scalar(count_stmt) or 0

        stmt = (
            select(PaymentModel)
            .options(
                selectinload(PaymentModel.items)
                .selectinload(PaymentItemModel.order_item)
                .selectinload(OrderItemModel.movie)
            )
            .where(
                PaymentModel.user_id == current_user.id,
            )
            .order_by(PaymentModel.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await db.execute(stmt)

        payments = result.scalars().all()

        total_pages = (
            (total + page_size - 1) // page_size
            if total
            else 1
        )

        return PaymentListResponseSchema(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            items=[
                PaymentService._to_payment_response(payment)
                for payment in payments
            ],
        )

    @staticmethod
    async def get_all_payments(
            db: AsyncSession,
            page: int,
            page_size: int,
            user_id: int | None = None,
            status: PaymentStatusEnum | None = None,
            created_from: datetime | None = None,
            created_to: datetime | None = None,
    ) -> PaymentListResponseSchema:

        count_stmt = select(func.count(PaymentModel.id))

        stmt = (
            select(PaymentModel)
            .options(
                selectinload(PaymentModel.items)
                .selectinload(PaymentItemModel.order_item)
                .selectinload(OrderItemModel.movie)
            )
        )

        if user_id is not None:
            count_stmt = count_stmt.where(
                PaymentModel.user_id == user_id,
            )

            stmt = stmt.where(
                PaymentModel.user_id == user_id,
            )

        if status is not None:
            count_stmt = count_stmt.where(
                PaymentModel.status == status,
            )

            stmt = stmt.where(
                PaymentModel.status == status,
            )

        if created_from is not None:
            count_stmt = count_stmt.where(
                PaymentModel.created_at >= created_from,
            )

            stmt = stmt.where(
                PaymentModel.created_at >= created_from,
            )

        if created_to is not None:
            count_stmt = count_stmt.where(
                PaymentModel.created_at <= created_to,
            )

            stmt = stmt.where(
                PaymentModel.created_at <= created_to,
            )

        total = await db.scalar(count_stmt) or 0

        stmt = (
            stmt
            .order_by(PaymentModel.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await db.execute(stmt)

        payments = result.scalars().all()

        total_pages = (
            (total + page_size - 1) // page_size
            if total
            else 1
        )

        return PaymentListResponseSchema(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            items=[
                PaymentService._to_payment_response(payment)
                for payment in payments
            ],
        )

    @staticmethod
    async def refund_payment(
            payment_uuid: str,
            current_user: UserModel,
            db: AsyncSession,
            stripe_service: StripeService,
    ) -> None:

        payment = await PaymentService._get_payment_or_404(
            payment_uuid=payment_uuid,
            current_user=current_user,
            db=db,
        )

        if payment.status == PaymentStatusEnum.REFUNDED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Payment has already been refunded.",
            )

        if payment.status != PaymentStatusEnum.SUCCESSFUL:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only successful payments can be refunded.",
            )

        if payment.external_payment_id is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="External payment ID is missing.",
            )

        stripe_service.create_refund(
            payment.external_payment_id,
        )

        payment.status = PaymentStatusEnum.REFUNDED

        payment.order.status = OrderStatusEnum.CANCELED

        await db.commit()

        send_payment_refunded_email_task.delay(
            payment.id,
        )

    @staticmethod
    async def cancel_payment(
            payment_uuid: str,
            db: AsyncSession,
    ) -> None:

        stmt = (
            select(PaymentModel)
            .options(
                selectinload(PaymentModel.order),
            )
            .where(
                PaymentModel.uuid == payment_uuid,
            )
        )

        result = await db.execute(stmt)

        payment = result.scalar_one_or_none()

        if payment is None:
            return

        if payment.status != PaymentStatusEnum.PENDING:
            return

        payment.status = PaymentStatusEnum.CANCELED

        if payment.order is not None:
            payment.order.status = OrderStatusEnum.CANCELED

        await db.commit()
