from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from src.database.models.payments import PaymentStatusEnum
from src.schemas.orders import OrderMovieResponseSchema


class PaymentItemResponseSchema(BaseModel):
    id: int
    price_at_payment: Decimal

    movie: OrderMovieResponseSchema


class PaymentResponseSchema(BaseModel):
    uuid: str
    created_at: datetime
    status: PaymentStatusEnum
    amount: Decimal

    items: list[PaymentItemResponseSchema]


class PaymentListResponseSchema(BaseModel):
    total: int
    page: int = 1
    page_size: int = 10
    total_pages: int

    items: list[PaymentResponseSchema]


class CheckoutResponseSchema(BaseModel):
    checkout_url: str
