import stripe

from src.database.models.accounts import UserModel
from src.database.models.orders import OrderModel


class StripeService:

    def __init__(
        self,
        secret_key: str,
    ):
        stripe.api_key = secret_key

    async def create_checkout_session(
        self,
        order: OrderModel,
        current_user: UserModel,
    ) -> str:

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
                            item.movie.price * 100
                        ),
                    },
                    "quantity": 1,
                }
                for item in order.items
            ],
            success_url=(
                "http://localhost:3000/payment/success"
            ),
            cancel_url=(
                "http://localhost:3000/payment/cancel"
            ),
            metadata={
                "order_uuid": order.uuid,
                "user_id": current_user.id,
            },
        )

        return session.url
