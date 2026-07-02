from datetime import datetime
from decimal import Decimal

from src.notifications import EmailSenderInterface


class StubEmailSender(EmailSenderInterface):
    def __init__(self):
        self.sent_emails: list[dict] = []

    async def send_activation_email(
        self,
        email: str,
        activation_link: str,
    ) -> None:
        self.sent_emails.append(
            {
                "type": "activation",
                "email": email,
                "link": activation_link,
            }
        )

    async def send_activation_complete_email(
        self,
        email: str,
        login_link: str,
    ) -> None:
        self.sent_emails.append(
            {
                "type": "activation_complete",
                "email": email,
                "link": login_link,
            }
        )

    async def send_password_reset_email(
        self,
        email: str,
        reset_link: str,
    ) -> None:
        self.sent_emails.append(
            {
                "type": "password_reset",
                "email": email,
                "link": reset_link,
            }
        )

    async def send_password_reset_complete_email(
        self,
        email: str,
        login_link: str,
    ) -> None:
        self.sent_emails.append(
            {
                "type": "password_reset_complete",
                "email": email,
                "link": login_link,
            }
        )

    async def send_payment_success_email(
        self,
        email: str,
        payment_uuid: str,
        amount: str,
        payment_date: str,
        movies: list[str],
    ) -> None:
        self.sent_emails.append(
            {
                "type": "payment_success",
                "email": email,
            }
        )

    async def send_payment_refunded_email(
        self,
        email: str,
        payment_uuid: str,
        amount: Decimal,
        refund_date: datetime,
        movies: list[str],
    ) -> None:
        self.sent_emails.append(
            {
                "type": "payment_refunded",
                "email": email,
            }
        )

    async def send_comment_reply_email(
        self,
        email: str,
        username: str,
        movie_name: str,
        comment_text: str,
        reply_text: str,
    ) -> None:
        self.sent_emails.append(
            {
                "type": "comment_reply",
                "email": email,
            }
        )

    async def send_comment_like_email(
        self,
        email: str,
        username: str,
        movie_name: str,
        comment_text: str,
        liked_by: str,
    ) -> None:
        self.sent_emails.append(
            {
                "type": "comment_like",
                "email": email,
            }
        )
