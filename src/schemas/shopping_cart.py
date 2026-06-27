from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from src.schemas.movies import CDSGSchema


class CartMovieResponseSchema(BaseModel):
    uuid: str
    name: str
    year: int
    price: Decimal
    genres: list[CDSGSchema]

    model_config = {
        "from_attributes": True,
    }


class CartItemResponseSchema(BaseModel):
    id: int
    added_at: datetime

    movie: CartMovieResponseSchema

    model_config = {
        "from_attributes": True,
    }


class CartResponseSchema(BaseModel):
    total_movies: int
    total_price: Decimal

    items: list[CartItemResponseSchema]

    model_config = {
        "from_attributes": True,
    }
