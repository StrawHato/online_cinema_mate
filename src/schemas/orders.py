from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from src.database.models.orders import OrderStatusEnum


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


class OrderResponseSchema(BaseModel):
    uuid: str
    created_at: datetime

    status: OrderStatusEnum

    total_amount: Decimal

    items: list[OrderItemResponseSchema]

    model_config = {
        "from_attributes": True,
    }
