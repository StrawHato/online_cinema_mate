from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class CDSGSchema(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True
    }


class MovieBaseSchema(BaseModel):
    name: str
    year: int
    time: int
    imdb: Decimal
    votes: int = 0
    meta_score: int | None = None
    gross: Decimal | None = None
    description: str
    price: Decimal


class MovieCreateRequestSchema(MovieBaseSchema):
    certification: str

    genres: list[str]
    stars: list[str]
    directors: list[str]


class MovieResponseSchema(MovieBaseSchema):
    id: int
    uuid: str

    certification: CDSGSchema
    genres: list[CDSGSchema]
    stars: list[CDSGSchema]
    directors: list[CDSGSchema]

    model_config = {
        "from_attributes": True
    }


class MovieListResponseSchema(BaseModel):
    total: int
    page: int = 1
    page_size: int = 10
    total_pages: int

    items: list[MovieResponseSchema]


class MovieUpdateRequestSchema(MovieCreateRequestSchema):
    pass


class MovieRatingRequestSchema(BaseModel):
    rating: int = Field(
        ge=1,
        le=10,
    )


class MovieRatingResponseSchema(BaseModel):
    rating: int
    created_at: datetime

    model_config = {
        "from_attributes": True,
    }


class MovieRatingSummarySchema(BaseModel):
    average_rating: Decimal
    ratings_count: int

    model_config = {
        "from_attributes": True,
    }
