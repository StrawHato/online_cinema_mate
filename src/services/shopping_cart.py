from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.schemas.movies import CDSGSchema
from src.database.models.accounts import UserModel
from src.database.models.movies import MovieModel
from src.database.models.shopping_cart import (
    CartItemModel,
    CartModel,
)
from src.schemas.shopping_cart import (
    CartItemResponseSchema,
    CartMovieResponseSchema,
    CartResponseSchema,
)
from src.services.movies import MovieService


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

            await db.flush()
            await db.refresh(cart)

        return cart

    @staticmethod
    async def _get_cart_item(
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

    @staticmethod
    async def get_cart(
        current_user: UserModel,
        db: AsyncSession,
    ) -> CartResponseSchema:

        cart = await ShoppingCartService._get_or_create_cart(
            current_user=current_user,
            db=db,
        )

        total_price = Decimal("0")

        items = []

        for item in cart.items:

            total_price += item.movie.price

            items.append(
                CartItemResponseSchema(
                    id=item.id,
                    added_at=item.added_at,
                    movie=CartMovieResponseSchema(
                        uuid=item.movie.uuid,
                        name=item.movie.name,
                        year=item.movie.year,
                        price=item.movie.price,
                        genres=[
                            CDSGSchema.model_validate(genre)
                            for genre in item.movie.genres
                        ],
                    ),
                )
            )

        return CartResponseSchema(
            total_movies=len(items),
            total_price=total_price,
            items=items,
        )

    @staticmethod
    async def add_movie_to_cart(
        movie_uuid: str,
        current_user: UserModel,
        db: AsyncSession,
    ) -> None:

        movie = await MovieService._get_movie_or_404(
            movie_uuid,
            db,
        )

        cart = await ShoppingCartService._get_or_create_cart(
            current_user=current_user,
            db=db,
        )

        existing = await ShoppingCartService._get_cart_item(
            cart.id,
            movie.id,
            db,
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Movie is already in cart.",
            )

        cart_item = CartItemModel(
            cart_id=cart.id,
            movie_id=movie.id,
        )

        db.add(cart_item)

        await db.commit()

    @staticmethod
    async def remove_movie_from_cart(
        movie_uuid: str,
        current_user: UserModel,
        db: AsyncSession,
    ) -> None:

        movie = await MovieService._get_movie_or_404(
            movie_uuid,
            db,
        )

        cart = await ShoppingCartService._get_or_create_cart(
            current_user=current_user,
            db=db,
        )

        cart_item = await ShoppingCartService._get_cart_item(
            cart.id,
            movie.id,
            db,
        )

        if cart_item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Movie is not in cart.",
            )

        await db.delete(cart_item)

        await db.commit()

    @staticmethod
    async def clear_cart(
        current_user: UserModel,
        db: AsyncSession,
    ) -> None:

        cart = await ShoppingCartService._get_or_create_cart(
            current_user=current_user,
            db=db,
        )

        for item in cart.items:
            await db.delete(item)

        await db.commit()
