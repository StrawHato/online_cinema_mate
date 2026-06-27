from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.movies import (
    GenreModel,
    MovieGenresTable,
)
from src.schemas.genres import (
    GenreCreateRequestSchema,
    GenreDetailResponseSchema,
    GenreResponseSchema,
    GenreUpdateRequestSchema,
)


class GenreService:
    @staticmethod
    async def create_genre(
        db: AsyncSession,
        genre_data: GenreCreateRequestSchema,
    ) -> GenreDetailResponseSchema:

        stmt = select(GenreModel).where(
            GenreModel.name == genre_data.name
        )

        result = await db.execute(stmt)

        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Genre already exists.",
            )

        genre = GenreModel(
            name=genre_data.name,
        )

        db.add(genre)

        await db.commit()
        await db.refresh(genre)

        return GenreDetailResponseSchema.model_validate(
            genre
        )

    @staticmethod
    async def get_genre(
        genre_id: int,
        db: AsyncSession,
    ) -> GenreDetailResponseSchema:

        stmt = select(GenreModel).where(
            GenreModel.id == genre_id
        )

        result = await db.execute(stmt)

        genre = result.scalar_one_or_none()

        if genre is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Genre not found.",
            )

        return GenreDetailResponseSchema.model_validate(
            genre
        )

    @staticmethod
    async def get_genres(
        db: AsyncSession,
    ) -> list[GenreResponseSchema]:

        stmt = (
            select(
                GenreModel.id,
                GenreModel.name,
                func.count(
                    MovieGenresTable.c.movie_id
                ).label(
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

    @staticmethod
    async def update_genre(
            genre_id: int,
            genre_data: GenreUpdateRequestSchema,
            db: AsyncSession,
    ) -> GenreDetailResponseSchema:

        stmt = select(GenreModel).where(
            GenreModel.id == genre_id
        )

        result = await db.execute(stmt)

        genre = result.scalar_one_or_none()

        if genre is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Genre not found.",
            )

        if genre_data.name is not None:

            stmt = (
                select(GenreModel)
                .where(
                    GenreModel.name == genre_data.name,
                    GenreModel.id != genre_id,
                )
            )

            result = await db.execute(stmt)

            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Genre already exists.",
                )

            genre.name = genre_data.name

        await db.commit()
        await db.refresh(genre)

        return GenreDetailResponseSchema.model_validate(
            genre
        )

    @staticmethod
    async def delete_genre(
            genre_id: int,
            db: AsyncSession,
    ) -> None:

        stmt = (
            select(GenreModel)
            .where(
                GenreModel.id == genre_id
            )
        )

        result = await db.execute(stmt)

        genre = result.scalar_one_or_none()

        if genre is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Genre not found.",
            )

        stmt = (
            select(func.count())
            .select_from(MovieGenresTable)
            .where(
                MovieGenresTable.c.genre_id == genre_id
            )
        )

        result = await db.execute(stmt)

        movies_count = result.scalar_one()

        if movies_count > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Genre cannot be deleted because "
                    "it is assigned to one or more movies."
                ),
            )

        await db.delete(genre)
        await db.commit()
