from decimal import Decimal

from fastapi import (
    APIRouter,
    Depends,
    status,
    Query,
    Response
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.movies import MovieSortEnum
from src.schemas.movies import MovieListResponseSchema
from src.services.movies import MovieService
from src.database.models.accounts import UserModel
from src.database.session import get_db
from src.config.dependencies import get_storage
from src.schemas.profile import (
    ProfileResponseSchema,
    ProfileUpdateRequestSchema,
)
from src.security.http import get_current_user
from src.services.profile import ProfileService
from src.storages.interfaces import StorageInterface


router = APIRouter(
    prefix="/profile",
    tags=["Profile"],
)


@router.get(
    "/",
    response_model=ProfileResponseSchema,
    summary="Get current user profile",
    status_code=status.HTTP_200_OK,
)
async def get_profile(
    current_user: UserModel = Depends(get_current_user),
) -> ProfileResponseSchema:
    return await ProfileService.get_profile(
        current_user=current_user,
    )


@router.patch(
    "/",
    response_model=ProfileResponseSchema,
    summary="Update current user profile",
    status_code=status.HTTP_200_OK,
)
async def update_profile(
    profile_data: ProfileUpdateRequestSchema = Depends(
        ProfileUpdateRequestSchema.from_form
    ),
    db: AsyncSession = Depends(get_db),
    storage: StorageInterface = Depends(get_storage),
    current_user: UserModel = Depends(get_current_user),
) -> ProfileResponseSchema:
    return await ProfileService.update_profile(
        db=db,
        storage=storage,
        current_user=current_user,
        profile_data=profile_data,
    )


@router.get(
    "/favorites/",
    response_model=MovieListResponseSchema,
)
async def get_favorite_movies(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=20),
    search: str | None = None,
    genre: str | None = None,
    director: str | None = None,
    star: str | None = None,
    year: int | None = None,
    imdb_min: Decimal | None = None,
    imdb_max: Decimal | None = None,
    sort: MovieSortEnum = MovieSortEnum.NAME_ASC,
):

    return await MovieService.get_movies(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        genre=genre,
        director=director,
        star=star,
        year=year,
        imdb_min=imdb_min,
        imdb_max=imdb_max,
        sort=sort,
        favorite_user_id=current_user.id,
    )


@router.post(
    "/favorites/{movie_uuid}/",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def add_to_favorites(
    movie_uuid: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):

    await MovieService.add_to_favorites(
        movie_uuid=movie_uuid,
        current_user=current_user,
        db=db,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/favorites/{movie_uuid}/",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_from_favorites(
    movie_uuid: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):

    await MovieService.remove_from_favorites(
        movie_uuid=movie_uuid,
        current_user=current_user,
        db=db,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
