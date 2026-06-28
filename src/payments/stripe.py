from decimal import Decimal

import stripe
from stripe import (
    SignatureVerificationError,
    StripeError,
)

from fastapi import HTTPException, status

from src.database.models.accounts import UserModel
from src.database.models.orders import OrderModel


class StripeService:
    def __init__(
        self,
        secret_key: str,
        webhook_secret: str,
        success_url: str,
        cancel_url: str,
    ):
        stripe.api_key = secret_key

        self.webhook_secret = webhook_secret
        self.success_url = success_url
        self.cancel_url = cancel_url

    def create_checkout_session(
        self,
        order: OrderModel,
        current_user: UserModel,
    ) -> str:

        try:
            session = stripe.checkout.Session.create(
                mode="payment",
                customer_email=current_user.email,
                line_items=[
                    {
                        "price_data": {
                            "currency": "usd",
                            "product_data": {
                                "name": item.movie.name,
                            },
                            "unit_amount": int(
                                Decimal(item.movie.price) * 100
                            ),
                        },
                        "quantity": 1,
                    }
                    for item in order.items
                ],
                metadata={
                    "order_uuid": order.uuid,
                    "user_id": str(current_user.id),
                },
                success_url=self.success_url,
                cancel_url=self.cancel_url,
            )

            return session.url

        except StripeError as error:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(error),
            )

    def verify_webhook(
        self,
        payload: bytes,
        signature: str,
    ) -> stripe.Event:

        try:
            return stripe.Webhook.construct_event(
                payload=payload,
                sig_header=signature,
                secret=self.webhook_secret,
            )

        except SignatureVerificationError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Stripe signature.",
            )

        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid webhook payload.",
            )
