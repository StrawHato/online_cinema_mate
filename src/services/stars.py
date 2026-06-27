from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.movies import (
    MovieStarsTable,
    StarModel,
)
from src.schemas.stars import (
    StarCreateRequestSchema,
    StarDetailResponseSchema,
    StarResponseSchema,
    StarUpdateRequestSchema,
)


class StarService:

    @staticmethod
    async def _get_star_or_404(
        star_id: int,
        db: AsyncSession,
    ) -> StarModel:

        stmt = select(StarModel).where(
            StarModel.id == star_id
        )

        result = await db.execute(stmt)

        star = result.scalar_one_or_none()

        if star is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Star not found.",
            )

        return star

    @staticmethod
    async def get_stars(
        db: AsyncSession,
    ) -> list[StarResponseSchema]:

        stmt = (
            select(
                StarModel.id,
                StarModel.name,
                func.count(
                    MovieStarsTable.c.movie_id
                ).label("movies_count"),
            )
            .outerjoin(
                MovieStarsTable,
                StarModel.id == MovieStarsTable.c.star_id,
            )
            .group_by(
                StarModel.id,
                StarModel.name,
            )
            .order_by(
                StarModel.name,
            )
        )

        result = await db.execute(stmt)

        return [
            StarResponseSchema(
                id=row.id,
                name=row.name,
                movies_count=row.movies_count,
            )
            for row in result.all()
        ]

    @staticmethod
    async def get_star(
        star_id: int,
        db: AsyncSession,
    ) -> StarDetailResponseSchema:

        star = await StarService._get_star_or_404(
            star_id,
            db,
        )

        return StarDetailResponseSchema.model_validate(
            star
        )

    @staticmethod
    async def create_star(
        star_data: StarCreateRequestSchema,
        db: AsyncSession,
    ) -> StarDetailResponseSchema:

        stmt = select(StarModel).where(
            StarModel.name == star_data.name
        )

        result = await db.execute(stmt)

        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Star already exists.",
            )

        star = StarModel(
            name=star_data.name,
        )

        db.add(star)

        await db.commit()
        await db.refresh(star)

        return StarDetailResponseSchema.model_validate(
            star
        )

    @staticmethod
    async def update_star(
        star_id: int,
        star_data: StarUpdateRequestSchema,
        db: AsyncSession,
    ) -> StarDetailResponseSchema:

        star = await StarService._get_star_or_404(
            star_id,
            db,
        )

        if star_data.name is not None:

            stmt = (
                select(StarModel)
                .where(
                    StarModel.name == star_data.name,
                    StarModel.id != star_id,
                )
            )

            result = await db.execute(stmt)

            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Star already exists.",
                )

            star.name = star_data.name

        await db.commit()
        await db.refresh(star)

        return StarDetailResponseSchema.model_validate(
            star
        )

    @staticmethod
    async def delete_star(
        star_id: int,
        db: AsyncSession,
    ) -> None:

        star = await StarService._get_star_or_404(
            star_id,
            db,
        )

        stmt = (
            select(func.count())
            .select_from(MovieStarsTable)
            .where(
                MovieStarsTable.c.star_id == star_id
            )
        )

        result = await db.execute(stmt)

        movies_count = result.scalar_one()

        if movies_count > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Star cannot be deleted because "
                    "it is assigned to one or more movies."
                ),
            )

        await db.delete(star)

        await db.commit()
