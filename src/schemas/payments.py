from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from src.database.models.payments import PaymentStatusEnum
from src.schemas.orders import OrderMovieResponseSchema


class PaymentItemResponseSchema(BaseModel):
    id: int
    price_at_payment: Decimal

    movie: OrderMovieResponseSchema

    model_config = {
        "from_attributes": True,
    }


class PaymentResponseSchema(BaseModel):
    uuid: str
    created_at: datetime
    status: PaymentStatusEnum
    amount: Decimal

    items: list[PaymentItemResponseSchema]

    model_config = {
        "from_attributes": True,
    }


class PaymentListResponseSchema(BaseModel):
    total: int
    page: int = 1
    page_size: int = 10
    total_pages: int

    items: list[PaymentResponseSchema]

    model_config = {
        "from_attributes": True,
    }


class CheckoutResponseSchema(BaseModel):
    checkout_url: str
