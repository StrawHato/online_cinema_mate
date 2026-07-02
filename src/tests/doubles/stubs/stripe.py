class StubStripeService:
    def create_checkout_session(
        self,
        order,
        payment,
        current_user,
    ) -> str:
        return "https://stripe.test/checkout"

    def verify_webhook(
        self,
        payload: bytes,
        signature: str,
    ):
        return {}

    def create_refund(
        self,
        payment_intent_id: str,
    ):
        return {}
