from decimal import Decimal

from pydantic import BaseModel

from src.schemas.orders import OrderMovieResponseSchema


class PaymentItemResponseSchema(BaseModel):
    id: int
    price_at_payment: Decimal

    order_item: OrderMovieResponseSchema
