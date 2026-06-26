from decimal import Decimal

from fastapi import (
    APIRouter,
    Depends,
    status, Query,
)
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.movies import MovieSortEnum
from src.database.session import get_db
from src.schemas.movies import (
    MovieCreateRequestSchema,
    MovieResponseSchema,
    MovieListResponseSchema,
    MovieUpdateRequestSchema,
)
from src.security.http import get_current_admin
from src.database.models.accounts import UserModel
from src.services.movies import MovieService

router = APIRouter(
    prefix="/movies",
    tags=["Movie"],
)


@router.post(
    "/",
    response_model=MovieResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create movie",
)
async def create_movie(
    movie_data: MovieCreateRequestSchema,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin),
) -> MovieResponseSchema:
    """
    Create a new movie.

    Only administrators are allowed to create movies.
    If a referenced certification, genre, director or star
    does not exist, it will be created automatically.
    """

    return await MovieService.create_movie(
        db=db,
        movie_data=movie_data,
    )


@router.get(
    "/{movie_uuid}/",
    response_model=MovieResponseSchema,
    summary="Get movie",
)
async def get_movie(
    movie_uuid: str,
    db: AsyncSession = Depends(get_db),
) -> MovieResponseSchema:

    return await MovieService.get_movie(
        db=db,
        movie_uuid=movie_uuid,
    )


@router.get(
    "/",
    response_model=MovieListResponseSchema,
    summary="Movie catalog",
)
async def get_movies(
    db: AsyncSession = Depends(get_db),
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
) -> MovieListResponseSchema:

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
    )


@router.patch(
    "/{movie_id}/",
    response_model=MovieResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def update_movie(
    movie_id: int,
    movie_data: MovieUpdateRequestSchema,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin),
) -> MovieResponseSchema:

    return await MovieService.update_movie(
        movie_id=movie_id,
        movie_data=movie_data,
        db=db,
    )
