from fastapi import (
    APIRouter,
    Depends,
    Query,
    Response,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.accounts import UserModel
from src.database.session import get_db
from src.schemas.orders import (
    OrderListResponseSchema,
    OrderResponseSchema,
)
from src.security.http import get_current_user
from src.services.orders import OrderService


router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
)


@router.post(
    "/",
    response_model=OrderResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create order",
)
async def create_order(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> OrderResponseSchema:

    return await OrderService.create_order(
        current_user=current_user,
        db=db,
    )
