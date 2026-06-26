from fastapi import (
    APIRouter,
    Depends,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.session import get_db
from src.schemas.movies import (
    MovieCreateRequestSchema,
    MovieResponseSchema,
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
