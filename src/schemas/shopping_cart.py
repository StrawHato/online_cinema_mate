from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class CartMovieResponseSchema(BaseModel):
    uuid: str
    name: str
    year: int
    price: Decimal
    genres: list[str]

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
