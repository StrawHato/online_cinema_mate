from fastapi import (
    APIRouter,
    Depends,
    Response,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.accounts import UserModel
from src.database.session import get_db
from src.schemas.stars import (
    StarCreateRequestSchema,
    StarDetailResponseSchema,
    StarResponseSchema,
    StarUpdateRequestSchema,
)
from src.security.http import get_current_admin
from src.services.stars import StarService


router = APIRouter(
    prefix="/stars",
    tags=["Stars"],
)


@router.get(
    "/",
    response_model=list[StarResponseSchema],
)
async def get_stars(
    db: AsyncSession = Depends(get_db),
):

    return await StarService.get_stars(
        db=db,
    )


@router.get(
    "/{star_id}/",
    response_model=StarDetailResponseSchema,
)
async def get_star(
    star_id: int,
    db: AsyncSession = Depends(get_db),
):

    return await StarService.get_star(
        star_id=star_id,
        db=db,
    )


@router.post(
    "/",
    response_model=StarDetailResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_star(
    star_data: StarCreateRequestSchema,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin),
):

    return await StarService.create_star(
        star_data=star_data,
        db=db,
    )


@router.patch(
    "/{star_id}/",
    response_model=StarDetailResponseSchema,
)
async def update_star(
    star_id: int,
    star_data: StarUpdateRequestSchema,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin),
):

    return await StarService.update_star(
        star_id=star_id,
        star_data=star_data,
        db=db,
    )


@router.delete(
    "/{star_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_star(
    star_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin),
) -> Response:

    await StarService.delete_star(
        star_id=star_id,
        db=db,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )
