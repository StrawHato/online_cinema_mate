from fastapi import (
    APIRouter,
    Depends,
    Response,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.accounts import UserModel
from src.database.session import get_db
from src.schemas.shopping_cart import CartResponseSchema
from src.security.http import get_current_user
from src.services.shopping_cart import ShoppingCartService


router = APIRouter(
    prefix="/cart",
    tags=["Shopping Cart"],
)


@router.get(
    "/",
    response_model=CartResponseSchema,
)
async def get_cart(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):

    return await ShoppingCartService.get_cart(
        current_user=current_user,
        db=db,
    )


@router.post(
    "/{movie_uuid}/",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def add_movie_to_cart(
    movie_uuid: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> Response:

    await ShoppingCartService.add_movie_to_cart(
        movie_uuid=movie_uuid,
        current_user=current_user,
        db=db,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )


@router.delete(
    "/{movie_uuid}/",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_movie_from_cart(
    movie_uuid: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> Response:

    await ShoppingCartService.remove_movie_from_cart(
        movie_uuid=movie_uuid,
        current_user=current_user,
        db=db,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )


@router.delete(
    "/clear/",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def clear_cart(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> Response:

    await ShoppingCartService.clear_cart(
        current_user=current_user,
        db=db,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )
