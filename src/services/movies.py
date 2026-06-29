from decimal import Decimal
from math import ceil

from fastapi import HTTPException, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models.orders import (
    OrderItemModel,
    OrderModel,
    OrderStatusEnum
)
from src.database.models.accounts import UserModel
from src.schemas.movies import (
    MovieResponseSchema,
    MovieCreateRequestSchema,
    MovieListResponseSchema,
    MovieUpdateRequestSchema, MovieRatingRequestSchema,
)
from src.database.models.movies import (
    CertificationModel,
    GenreModel,
    StarModel,
    DirectorModel,
    MovieModel,
    MovieSortEnum,
    UserFavoriteMovieModel,
    MovieRatingModel,
)


SORT_MAPPING = {
    MovieSortEnum.NAME_ASC: MovieModel.name.asc(),
    MovieSortEnum.NAME_DESC: MovieModel.name.desc(),

    MovieSortEnum.YEAR_ASC: MovieModel.year.asc(),
    MovieSortEnum.YEAR_DESC: MovieModel.year.desc(),

    MovieSortEnum.PRICE_ASC: MovieModel.price.asc(),
    MovieSortEnum.PRICE_DESC: MovieModel.price.desc(),

    MovieSortEnum.IMDB_ASC: MovieModel.imdb.asc(),
    MovieSortEnum.IMDB_DESC: MovieModel.imdb.desc(),

    MovieSortEnum.POPULARITY_ASC: MovieModel.votes.asc(),
    MovieSortEnum.POPULARITY_DESC: MovieModel.votes.desc(),
}


class MovieService:

    @staticmethod
    async def get_or_create_certification(
            certification_name: str,
            db: AsyncSession,
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
    async def get_or_create_genres(
            genres: list[str],
            db: AsyncSession,
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
    async def get_or_create_stars(
            stars: list[str],
            db: AsyncSession,
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
    async def get_or_create_directors(
            directors: list[str],
            db: AsyncSession,
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
    async def _get_movie_or_404(
            movie_uuid: str,
            db: AsyncSession,
    ) -> MovieModel:

        stmt = (
            select(MovieModel)
            .options(
                selectinload(MovieModel.certification),
                selectinload(MovieModel.genres),
                selectinload(MovieModel.stars),
                selectinload(MovieModel.directors),
            )
            .where(
                MovieModel.uuid == movie_uuid,
            )
        )

        result = await db.execute(stmt)

        movie = result.scalar_one_or_none()

        if movie is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Movie not found.",
            )

        return movie

    @staticmethod
    async def _recalculate_rating(
            movie: MovieModel,
            db: AsyncSession,
    ) -> None:
        stmt = (
            select(
                func.avg(MovieRatingModel.rating),
                func.count(MovieRatingModel.id),
            )
            .where(
                MovieRatingModel.movie_id == movie.id,
            )
        )

        result = await db.execute(stmt)

        average, count = result.one()

        movie.average_rating = round(
            average or 0,
            2,
        )

        movie.ratings_count = count

    @staticmethod
    async def create_movie(
            movie_data: MovieCreateRequestSchema,
            db: AsyncSession,
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

        certification = await MovieService.get_or_create_certification(
            db=db,
            certification_name=movie_data.certification,
        )

        genres = await MovieService.get_or_create_genres(
            db=db,
            genres=movie_data.genres,
        )

        stars = await MovieService.get_or_create_stars(
            db=db,
            stars=movie_data.stars,
        )

        directors = await MovieService.get_or_create_directors(
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

    @staticmethod
    async def get_movie(
            movie_uuid: str,
            db: AsyncSession,
    ) -> MovieResponseSchema:
        movie = await MovieService._get_movie_or_404(db=db, movie_uuid=movie_uuid)
        return MovieResponseSchema.model_validate(movie)

    @staticmethod
    async def get_movies(
            db: AsyncSession,
            page: int = 1,
            page_size: int = 20,
            search: str | None = None,
            genre: str | None = None,
            director: str | None = None,
            star: str | None = None,
            year: int | None = None,
            imdb_min: Decimal | None = None,
            imdb_max: Decimal | None = None,
            sort: MovieSortEnum = MovieSortEnum.NAME_ASC,
            favorite_user_id: int | None = None
    ) -> MovieListResponseSchema:

        stmt = (
            select(MovieModel)
            .options(
                selectinload(MovieModel.certification),
                selectinload(MovieModel.genres),
                selectinload(MovieModel.stars),
                selectinload(MovieModel.directors),
            )
        )

        if favorite_user_id:
            stmt = (
                stmt
                .join(
                    UserFavoriteMovieModel,
                    UserFavoriteMovieModel.movie_id == MovieModel.id,
                )
                .where(
                    UserFavoriteMovieModel.user_id == favorite_user_id,
                )
            )

        if search:
            stmt = (
                stmt.outerjoin(MovieModel.directors)
                .outerjoin(MovieModel.stars)
                .where(
                    or_(
                        MovieModel.name.ilike(f"%{search}%"),
                        MovieModel.description.ilike(f"%{search}%"),
                        DirectorModel.name.ilike(f"%{search}%"),
                        StarModel.name.ilike(f"%{search}%"),
                    )
                )
            )

        if genre:
            stmt = (
                stmt.join(MovieModel.genres)
                .where(GenreModel.name == genre)
            )

        if director:
            stmt = (
                stmt.join(MovieModel.directors)
                .where(DirectorModel.name == director)
            )

        if star:
            stmt = (
                stmt.join(MovieModel.stars)
                .where(StarModel.name == star)
            )

        if year is not None:
            stmt = stmt.where(
                MovieModel.year == year
            )

        if imdb_min is not None:
            stmt = stmt.where(
                MovieModel.imdb >= imdb_min
            )

        if imdb_max is not None:
            stmt = stmt.where(
                MovieModel.imdb <= imdb_max
            )

        stmt = stmt.order_by(
            SORT_MAPPING[sort]
        )

        total_stmt = (
            select(func.count())
            .select_from(stmt.subquery())
        )

        total = await db.scalar(total_stmt)

        stmt = (
            stmt.offset(
                (page - 1) * page_size
            )
            .limit(page_size)
        )

        result = await db.execute(stmt)

        movies = result.scalars().unique().all()

        total_pages = max(1, ceil(total / page_size))

        if page > total_pages:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Page not found.",
            )

        return MovieListResponseSchema(
            items=[
                MovieResponseSchema.model_validate(movie)
                for movie in movies
            ],
            page=page,
            page_size=page_size,
            total=total or 0,
            total_pages=total_pages,
        )

    @staticmethod
    async def get_movie_by_name_and_year(
            db: AsyncSession,
            name: str,
            year: int,
    ) -> MovieModel | None:

        stmt = select(MovieModel).where(
            MovieModel.name == name,
            MovieModel.year == year,
        )

        result = await db.execute(stmt)

        return result.scalar_one_or_none()

    @staticmethod
    async def update_movie(
            movie_id: int,
            movie_data: MovieUpdateRequestSchema,
            db: AsyncSession,
    ) -> MovieResponseSchema:

        stmt = (
            select(MovieModel)
            .options(
                selectinload(MovieModel.certification),
                selectinload(MovieModel.genres),
                selectinload(MovieModel.stars),
                selectinload(MovieModel.directors),
            )
            .where(MovieModel.id == movie_id)
        )

        result = await db.execute(stmt)

        movie = result.scalar_one_or_none()

        if movie is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Movie not found.",
            )

        data = movie_data.model_dump(
            exclude_unset=True,
            exclude={
                "certification",
                "genres",
                "stars",
                "directors",
            },
        )

        for field, value in data.items():
            setattr(movie, field, value)

        if movie_data.certification is not None:
            movie.certification = (
                await MovieService.get_or_create_certification(
                    movie_data.certification,
                    db,
                )
            )

        if movie_data.genres is not None:
            movie.genres = (
                await MovieService.get_or_create_genres(
                    movie_data.genres,
                    db,
                )
            )

        if movie_data.stars is not None:
            movie.stars = (
                await MovieService.get_or_create_stars(
                    movie_data.stars,
                    db,
                )
            )

        if movie_data.directors is not None:
            movie.directors = (
                await MovieService.get_or_create_directors(
                    movie_data.directors,
                    db,
                )
            )

        await db.commit()

        await db.refresh(movie)

        return MovieResponseSchema.model_validate(movie)

    @staticmethod
    async def delete_movie(
            movie_id: int,
            db: AsyncSession,
    ) -> None:

        stmt = select(MovieModel).where(
            MovieModel.id == movie_id
        )

        result = await db.execute(stmt)

        movie = result.scalar_one_or_none()

        if movie is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Movie not found.",
            )

        stmt = (
            select(OrderItemModel.id)
            .join(OrderModel)
            .where(
                OrderItemModel.movie_id == movie.id,
                OrderModel.status == OrderStatusEnum.PAID,
            )
        )

        result = await db.execute(stmt.limit(1))

        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Movie cannot be deleted because it "
                    "has already been purchased."
                ),
            )

        await db.delete(movie)
        await db.commit()

    @staticmethod
    async def add_to_favorites(
            movie_uuid: str,
            current_user: UserModel,
            db: AsyncSession,
    ) -> None:

        movie = await MovieService._get_movie_or_404(
            movie_uuid,
            db,
        )

        stmt = (
            select(UserFavoriteMovieModel)
            .where(
                UserFavoriteMovieModel.user_id == current_user.id,
                UserFavoriteMovieModel.movie_id == movie.id,
            )
        )

        result = await db.execute(stmt)

        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Movie is already in favorites.",
            )

        favorite = UserFavoriteMovieModel(
            user_id=current_user.id,
            movie_id=movie.id,
        )

        db.add(favorite)

        await db.commit()

    @staticmethod
    async def remove_from_favorites(
            movie_uuid: str,
            current_user: UserModel,
            db: AsyncSession,
    ) -> None:

        movie = await MovieService._get_movie_or_404(
            movie_uuid,
            db,
        )

        stmt = (
            select(UserFavoriteMovieModel)
            .where(
                UserFavoriteMovieModel.user_id == current_user.id,
                UserFavoriteMovieModel.movie_id == movie.id,
            )
        )

        result = await db.execute(stmt)

        favorite = result.scalar_one_or_none()

        if favorite is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Movie is not in favorites.",
            )

        await db.delete(favorite)

        await db.commit()
