from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models.accounts import UserModel
from src.database.models.movies import MovieModel
from src.database.models.shopping_cart import (
    CartItemModel,
    CartModel,
)


class ShoppingCartService:
    @staticmethod
    async def _get_or_create_cart(
        current_user: UserModel,
        db: AsyncSession,
    ) -> CartModel:

        stmt = (
            select(CartModel)
            .options(
                selectinload(CartModel.items)
                .selectinload(CartItemModel.movie)
                .selectinload(MovieModel.genres)
            )
            .where(
                CartModel.user_id == current_user.id
            )
        )

        result = await db.execute(stmt)

        cart = result.scalar_one_or_none()

        if cart is None:
            cart = CartModel(
                user_id=current_user.id,
            )

            db.add(cart)

            await db.commit()
            await db.refresh(cart)

        return cart

    @staticmethod
    async def _get_cart_item_or_404(
        cart_id: int,
        movie_id: int,
        db: AsyncSession,
    ) -> CartItemModel | None:

        stmt = (
            select(CartItemModel)
            .where(
                CartItemModel.cart_id == cart_id,
                CartItemModel.movie_id == movie_id,
            )
        )

        result = await db.execute(stmt)

        return result.scalar_one_or_none()
