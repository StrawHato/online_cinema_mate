from decimal import Decimal

from pydantic import BaseModel


class CDSGSchema(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True
    }


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


class MovieResponseSchema(MovieCreateRequestSchema):
    certification: CDSGSchema
    genres: list[CDSGSchema]
    stars: list[CDSGSchema]
    directors: list[CDSGSchema]

    model_config = {
        "from_attributes": True
    }
