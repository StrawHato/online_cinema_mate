from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models.base import Base


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
