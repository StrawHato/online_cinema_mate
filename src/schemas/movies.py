from decimal import Decimal

from pydantic import BaseModel


class CDSGSchema(BaseModel):
    id: int
    name: str


class MovieCreateRequestSchema(BaseModel):
    name: str
    year: int
    time: int
    imdb: Decimal
    votes: int = 0
    meta_score: int | None
    gross: Decimal | None
    description: str
    price: Decimal

    certification: str

    genres: list[str]
    stars: list[str]
    directors: list[str]
