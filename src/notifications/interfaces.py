from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal


class EmailSenderInterface(ABC):

    @abstractmethod
    async def send_activation_email(self, email: str, activation_link: str) -> None:
        pass

    @abstractmethod
    async def send_activation_complete_email(self, email: str, login_link: str) -> None:
        pass

    @abstractmethod
    async def send_password_reset_email(self, email: str, reset_link: str) -> None:
        pass

    @abstractmethod
    async def send_password_reset_complete_email(self, email: str, login_link: str) -> None:
        pass

    @abstractmethod
    async def send_payment_success_email(
            self,
            email: str,
            payment_uuid: str,
            amount: str,
            payment_date: str,
            movies: list[str],
    ) -> None:
        pass

    @abstractmethod
    async def send_payment_refunded_email(
            self,
            email: str,
            payment_uuid: str,
            amount: Decimal,
            refund_date: datetime,
            movies: list[str],
    ) -> None:
        """
        Send a payment refunded email asynchronously.
        """
        pass

    @abstractmethod
    async def send_comment_reply_email(
        self,
        email: str,
        username: str,
        movie_name: str,
        comment_text: str,
        reply_text: str,
    ) -> None:
        """
        Notify a user that someone replied to their comment.
        """
        pass

    @abstractmethod
    async def send_comment_like_email(
        self,
        email: str,
        username: str,
        movie_name: str,
        comment_text: str,
        liked_by: str,
    ) -> None:
        """
        Notify a user that someone liked their comment.
        """
        pass
