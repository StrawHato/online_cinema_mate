from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.movies import GenreModel, MovieGenresTable
from src.schemas.genres import GenreResponseSchema


class GenreService:

    @staticmethod
    async def get_genres(
        db: AsyncSession,
    ) -> list[GenreResponseSchema]:

        stmt = (
            select(
                GenreModel.id,
                GenreModel.name,
                func.count(MovieGenresTable.c.movie_id).label(
                    "movies_count"
                ),
            )
            .outerjoin(
                MovieGenresTable,
                GenreModel.id == MovieGenresTable.c.genre_id,
            )
            .group_by(
                GenreModel.id,
                GenreModel.name,
            )
            .order_by(
                GenreModel.name,
            )
        )

        result = await db.execute(stmt)

        return [
            GenreResponseSchema(
                id=row.id,
                name=row.name,
                movies_count=row.movies_count,
            )
            for row in result.all()
        ]
