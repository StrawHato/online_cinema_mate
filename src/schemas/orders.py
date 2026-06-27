from decimal import Decimal

from pydantic import BaseModel


class OrderMovieResponseSchema(BaseModel):
    uuid: str
    name: str
    year: int

    model_config = {
        "from_attributes": True,
    }


class OrderItemResponseSchema(BaseModel):
    id: int
    price_at_order: Decimal

    movie: OrderMovieResponseSchema

    model_config = {
        "from_attributes": True,
    }
