from fastapi import (
    APIRouter,
    Depends,
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
