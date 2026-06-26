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
