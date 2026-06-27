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
