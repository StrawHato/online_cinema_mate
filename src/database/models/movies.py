from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    String,
    Column,
    ForeignKey,
    Table,
    Numeric,
    Text,
    Integer,
    CheckConstraint,
    DateTime,
    func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models.base import Base


class MovieSortEnum(str, Enum):
    NAME_ASC = "name"
    NAME_DESC = "-name"

    YEAR_ASC = "year"
    YEAR_DESC = "-year"

    PRICE_ASC = "price"
    PRICE_DESC = "-price"

    IMDB_ASC = "imdb"
    IMDB_DESC = "-imdb"

    POPULARITY_ASC = "votes"
    POPULARITY_DESC = "-votes"


class GenreModel(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    movies: Mapped[list["MovieModel"]] = relationship(
        secondary="movie_genres",
        back_populates="genres",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<Genre(id={self.id}, "
            f"name='{self.name}')>"
        )


class StarModel(Base):
    __tablename__ = "stars"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    movies: Mapped[list["MovieModel"]] = relationship(
        secondary="movie_stars",
        back_populates="stars",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<Star(id={self.id}, "
            f"name='{self.name}')>"
        )


class DirectorModel(Base):
    __tablename__ = "directors"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    movies: Mapped[list["MovieModel"]] = relationship(
        secondary="movie_directors",
        back_populates="directors",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<Director(id={self.id}, "
            f"name='{self.name}')>"
        )


class CertificationModel(Base):
    __tablename__ = "certifications"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
    )

    movies: Mapped[list["MovieModel"]] = relationship(
        back_populates="certification",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<Certification(id={self.id}, "
            f"name='{self.name}')>"
        )


MovieGenresTable = Table(
    "movie_genres",
    Base.metadata,
    Column(
        "movie_id",
        ForeignKey(
            "movies.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
        nullable=False,
    ),
    Column(
        "genre_id",
        ForeignKey(
            "genres.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
        nullable=False,
    ),
)


MovieStarsTable = Table(
    "movie_stars",
    Base.metadata,
    Column(
        "movie_id",
        ForeignKey(
            "movies.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
        nullable=False,
    ),
    Column(
        "star_id",
        ForeignKey(
            "stars.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
        nullable=False,
    ),
)


MovieDirectorsTable = Table(
    "movie_directors",
    Base.metadata,
    Column(
        "movie_id",
        ForeignKey(
            "movies.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
        nullable=False,
    ),
    Column(
        "director_id",
        ForeignKey(
            "directors.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
        nullable=False,
    ),
)


class MovieModel(Base):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    uuid: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid4()),
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    time: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    imdb: Mapped[Decimal] = mapped_column(
        Numeric(3,1),
        nullable=False,
        index=True,
    )

    votes: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    meta_score: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    gross: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    certification_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey(
            "certifications.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    certification: Mapped[Optional["CertificationModel"]] = relationship(
        back_populates="movies",
        lazy="selectin",
    )

    genres: Mapped[list["GenreModel"]] = relationship(
        secondary=MovieGenresTable,
        back_populates="movies",
        lazy="selectin",
    )

    directors: Mapped[list["DirectorModel"]] = relationship(
        secondary=MovieDirectorsTable,
        back_populates="movies",
        lazy="selectin",
    )

    stars: Mapped[list["StarModel"]] = relationship(
        secondary=MovieStarsTable,
        back_populates="movies",
        lazy="selectin",
    )

    favorite_users: Mapped[list["UserFavoriteMovieModel"]] = relationship(
        back_populates="movie",
        cascade="all, delete-orphan",
    )

    cart_items: Mapped[list["CartItemModel"]] = relationship(
        "CartItemModel",
        back_populates="movie",
    )

    __table_args__ = (
        CheckConstraint("imdb >= 0 AND imdb <= 10"),
        CheckConstraint("price >= 0"),
        CheckConstraint("votes >= 0"),
    )

    def __repr__(self) -> str:
        return (
            f"<Movie("
            f"id={self.id}, "
            f"name='{self.name}', "
            f"year={self.year}"
            f")>"
        )


class UserFavoriteMovieModel(Base):
    __tablename__ = "user_favorite_movies"

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    movie_id: Mapped[int] = mapped_column(
        ForeignKey(
            "movies.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    user: Mapped["UserModel"] = relationship(
        "UserModel",
        back_populates="favorite_movies",
        lazy="selectin",
    )

    movie: Mapped["MovieModel"] = relationship(
        "MovieModel",
        back_populates="favorite_users",
        lazy="selectin",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<UserFavoriteMovie("
            f"user_id={self.user_id}, "
            f"movie_id={self.movie_id}"
            f")>"
        )
