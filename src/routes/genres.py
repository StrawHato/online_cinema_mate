from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.genres import GenreResponseSchema
from src.services.genres import GenreService
from src.database.session import get_db


router = APIRouter(
    prefix="/genres",
    tags=["Genre"],
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
