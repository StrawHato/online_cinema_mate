from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models.movies import MovieModel
from src.database.models.accounts import UserModel
from src.database.models.orders import (
    OrderItemModel,
    OrderModel,
    OrderStatusEnum,
)
from src.schemas.orders import (
    OrderItemResponseSchema,
    OrderListResponseSchema,
    OrderMovieResponseSchema,
    OrderResponseSchema,
)
from src.services.shopping_cart import ShoppingCartService


class OrderService:

    @staticmethod
    async def _get_order_or_404(
        order_uuid: str,
        current_user: UserModel,
        db: AsyncSession,
    ) -> OrderModel:

        stmt = (
            select(OrderModel)
            .options(
                selectinload(OrderModel.items)
                .selectinload(OrderItemModel.movie)
            )
            .where(
                OrderModel.uuid == order_uuid,
                OrderModel.user_id == current_user.id,
            )
        )

        result = await db.execute(stmt)

        order = result.scalar_one_or_none()

        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found.",
            )

        return order

    @staticmethod
    def _to_order_response(
            order: OrderModel,
    ) -> OrderResponseSchema:

        return OrderResponseSchema(
            uuid=order.uuid,
            created_at=order.created_at,
            status=order.status,
            total_amount=order.total_amount,
            items=[
                OrderItemResponseSchema(
                    id=item.id,
                    price_at_order=item.price_at_order,
                    movie=OrderMovieResponseSchema(
                        uuid=item.movie.uuid,
                        name=item.movie.name,
                        year=item.movie.year,
                    ),
                )
                for item in order.items
            ],
        )

    @staticmethod
    def _calculate_actual_amount(
            order: OrderModel,
    ) -> Decimal:

        return sum(
            (
                item.movie.price
                for item in order.items
            ),
            start=Decimal("0"),
        )

    @staticmethod
    async def create_order(
        current_user: UserModel,
        db: AsyncSession,
    ) -> OrderResponseSchema:

        cart = await ShoppingCartService._get_or_create_cart(
            current_user=current_user,
            db=db,
        )

        if not cart.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Shopping cart is empty.",
            )

        movie_ids = [
            item.movie_id
            for item in cart.items
        ]

        stmt = (
            select(OrderItemModel.movie_id)
            .join(OrderModel)
            .where(
                OrderModel.user_id == current_user.id,
                OrderModel.status == OrderStatusEnum.PENDING,
                OrderItemModel.movie_id.in_(movie_ids),
            )
        )

        result = await db.execute(stmt.limit(1))

        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Some movies are already included "
                    "in another pending order."
                ),
            )

        # TODO:
        # Check already purchased movies.

        order = OrderModel(
            user_id=current_user.id,
        )

        db.add(order)

        await db.flush()

        total_amount = Decimal("0")

        for cart_item in cart.items:

            order_item = OrderItemModel(
                order_id=order.id,
                movie_id=cart_item.movie.id,
                price_at_order=cart_item.movie.price,
            )

            db.add(order_item)

            total_amount += cart_item.movie.price

        order.total_amount = total_amount

        for cart_item in cart.items:
            await db.delete(cart_item)

        await db.commit()
        await db.refresh(order, attribute_names=["items"])

        return OrderService._to_order_response(order)

    @staticmethod
    async def get_orders(
        current_user: UserModel,
        db: AsyncSession,
        page: int,
        page_size: int,
    ) -> OrderListResponseSchema:

        count_stmt = (
            select(func.count(OrderModel.id))
            .where(
                OrderModel.user_id == current_user.id,
            )
        )

        total = await db.scalar(count_stmt) or 0

        stmt = (
            select(OrderModel)
            .options(
                selectinload(OrderModel.items)
                .selectinload(OrderItemModel.movie)
            )
            .where(
                OrderModel.user_id == current_user.id,
            )
            .order_by(OrderModel.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await db.execute(stmt)

        orders = result.scalars().all()

        total_pages = (
            (total + page_size - 1) // page_size
            if total
            else 1
        )

        return OrderListResponseSchema(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            items=[
                OrderResponseSchema.model_validate(order)
                for order in orders
            ],
        )

    @staticmethod
    async def get_order(
            order_uuid: str,
            current_user: UserModel,
            db: AsyncSession,
    ) -> OrderResponseSchema:

        order = await OrderService._get_order_or_404(
            order_uuid=order_uuid,
            current_user=current_user,
            db=db,
        )

        return OrderService._to_order_response(order)

    @staticmethod
    async def cancel_order(
        order_uuid: str,
        current_user: UserModel,
        db: AsyncSession,
    ) -> None:

        order = await OrderService._get_order_or_404(
            order_uuid=order_uuid,
            current_user=current_user,
            db=db,
        )

        if order.status == OrderStatusEnum.PAID:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Paid orders cannot be canceled.",
            )

        if order.status == OrderStatusEnum.CANCELED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Order is already canceled.",
            )

        order.status = OrderStatusEnum.CANCELED

        await db.commit()

    @staticmethod
    async def get_all_orders(
            db: AsyncSession,
            page: int,
            page_size: int,
            user_id: int | None = None,
            status: OrderStatusEnum | None = None,
            created_from: datetime | None = None,
            created_to: datetime | None = None,
    ) -> OrderListResponseSchema:

        count_stmt = select(func.count(OrderModel.id))

        stmt = (
            select(OrderModel)
            .options(
                selectinload(OrderModel.items)
                .selectinload(OrderItemModel.movie)
            )
        )

        if user_id is not None:
            count_stmt = count_stmt.where(
                OrderModel.user_id == user_id,
            )

            stmt = stmt.where(
                OrderModel.user_id == user_id,
            )

        if status is not None:
            count_stmt = count_stmt.where(
                OrderModel.status == status,
            )

            stmt = stmt.where(
                OrderModel.status == status,
            )

        if created_from is not None:
            count_stmt = count_stmt.where(
                OrderModel.created_at >= created_from,
            )

            stmt = stmt.where(
                OrderModel.created_at >= created_from,
            )

        if created_to is not None:
            count_stmt = count_stmt.where(
                OrderModel.created_at <= created_to,
            )

            stmt = stmt.where(
                OrderModel.created_at <= created_to,
            )

        total = await db.scalar(count_stmt) or 0

        stmt = (
            stmt
            .order_by(OrderModel.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await db.execute(stmt)

        orders = result.scalars().all()

        total_pages = (
            (total + page_size - 1) // page_size
            if total
            else 1
        )

        return OrderListResponseSchema(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            items=[
                OrderService._to_order_response(order)
                for order in orders
            ],
        )
