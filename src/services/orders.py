from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models.movies import MovieModel
from src.database.models.accounts import UserModel
from src.database.models.orders import (
    OrderItemModel,
    OrderModel,
)
from src.schemas.orders import (
    OrderItemResponseSchema,
    OrderMovieResponseSchema,
    OrderResponseSchema,
)


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
                .selectinload(OrderItemModel.movie)
                .selectinload(MovieModel.genres)
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
