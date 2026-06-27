from fastapi import (
    APIRouter,
    Depends,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.accounts import UserModel
from src.database.session import get_db
from src.schemas.genres import (
    GenreCreateRequestSchema,
    GenreDetailResponseSchema,
    GenreResponseSchema,
)
from src.security.http import get_current_admin
from src.services.genres import GenreService


router = APIRouter(
    prefix="/genres",
    tags=["Genres"],
)


@router.get(
    "/",
    response_model=list[GenreResponseSchema],
    summary="Get genres list",
)
async def get_genres(
    db: AsyncSession = Depends(get_db),
) -> list[GenreResponseSchema]:

    return await GenreService.get_genres(db)


@router.get(
    "/{genre_id}/",
    response_model=GenreDetailResponseSchema,
)
async def get_genre(
    genre_id: int,
    db: AsyncSession = Depends(get_db),
):

    return await GenreService.get_genre(
        genre_id=genre_id,
        db=db,
    )


@router.post(
    "/",
    response_model=GenreDetailResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_genre(
    genre_data: GenreCreateRequestSchema,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin),
):

    return await GenreService.create_genre(
        db=db,
        genre_data=genre_data,
    )
