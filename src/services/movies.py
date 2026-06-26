from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.movies import MovieResponseSchema, MovieCreateRequestSchema
from src.database.models.movies import CertificationModel, GenreModel, StarModel, DirectorModel, MovieModel
from src.database.session import get_db


class MovieService:

    @staticmethod
    async def _get_or_create_certification(
            certification_name: str,
            db: AsyncSession = Depends(get_db),
    ) -> CertificationModel:
        stmt = select(CertificationModel).where(
            CertificationModel.name == certification_name
        )

        result = await db.execute(stmt)

        certification = result.scalar_one_or_none()

        if certification is None:
            certification = CertificationModel(
                name=certification_name,
            )

            db.add(certification)

            await db.flush()

        return certification

    @staticmethod
    async def _get_or_create_genres(
            genres: list[str],
            db: AsyncSession = Depends(get_db),
    ) -> list[GenreModel]:

        movie_genres = []

        for genre_name in genres:

            stmt = select(GenreModel).where(
                GenreModel.name == genre_name
            )

            result = await db.execute(stmt)

            genre = result.scalar_one_or_none()

            if genre is None:
                genre = GenreModel(
                    name=genre_name,
                )

                db.add(genre)

                await db.flush()

            movie_genres.append(genre)

        return movie_genres

    @staticmethod
    async def _get_or_create_stars(
            stars: list[str],
            db: AsyncSession = Depends(get_db),
    ) -> list[StarModel]:

        movie_stars = []

        for star_name in stars:

            stmt = select(StarModel).where(
                StarModel.name == star_name
            )

            result = await db.execute(stmt)

            star = result.scalar_one_or_none()

            if star is None:
                star = StarModel(
                    name=star_name,
                )

                db.add(star)

                await db.flush()

            movie_stars.append(star)

        return movie_stars

    @staticmethod
    async def _get_or_create_directors(
            directors: list[str],
            db: AsyncSession = Depends(get_db),
    ):
        movie_directors = []

        for director_name in directors:
            stmt = select(DirectorModel).where(
                DirectorModel.name == director_name
            )

            result = await db.execute(stmt)
            director = result.scalar_one_or_none()

            if director is None:
                director = DirectorModel(
                    name=director_name,
                )
                db.add(director)
                await db.flush()

            movie_directors.append(director)

        return movie_directors

    @staticmethod
    async def create(
            movie_data: MovieCreateRequestSchema,
            db: AsyncSession = Depends(get_db),
    ) -> MovieResponseSchema:

        stmt = select(MovieModel).where(
            MovieModel.name == movie_data.name,
            MovieModel.year == movie_data.year,
        )

        result = await db.execute(stmt)

        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Movie already exists.",
            )

        certification = await MovieService._get_or_create_certification(
            db=db,
            certification_name=movie_data.certification,
        )

        genres = await MovieService._get_or_create_genres(
            db=db,
            genres=movie_data.genres,
        )

        stars = await MovieService._get_or_create_stars(
            db=db,
            stars=movie_data.stars,
        )

        directors = await MovieService._get_or_create_directors(
            db=db,
            directors=movie_data.directors,
        )

        movie = MovieModel(
            name=movie_data.name,
            year=movie_data.year,
            time=movie_data.time,
            imdb=movie_data.imdb,
            votes=movie_data.votes,
            meta_score=movie_data.meta_score,
            gross=movie_data.gross,
            description=movie_data.description,
            price=movie_data.price,
            certification=certification,
            genres=genres,
            stars=stars,
            directors=directors,
        )

        db.add(movie)

        await db.commit()

        await db.refresh(movie)

        return MovieResponseSchema.model_validate(movie)
