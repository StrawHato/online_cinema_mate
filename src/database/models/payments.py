from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import uuid4

from sqlalchemy import (
    String,
    ForeignKey,
    CheckConstraint,
    Numeric,
    Enum as SQLEnum,
    DateTime,
    func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models.base import Base


class PaymentStatusEnum(str, Enum):
    PENDING = "pending"
    SUCCESSFUL = "successful"
    CANCELED = "canceled"
    REFUNDED = "refunded"


class PaymentModel(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    uuid: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid4()),
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    order_id: Mapped[int] = mapped_column(
        ForeignKey(
            "orders.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    status: Mapped[PaymentStatusEnum] = mapped_column(
        SQLEnum(
            PaymentStatusEnum,
            name="payment_status_enum",
        ),
        default=PaymentStatusEnum.PENDING,
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    external_payment_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
    )

    user: Mapped["UserModel"] = relationship(
        "UserModel",
        back_populates="payments",
        lazy="selectin",
    )

    order: Mapped["OrderModel"] = relationship(
        "OrderModel",
        back_populates="payments",
        lazy="selectin",
    )

    items: Mapped[list["PaymentItemModel"]] = relationship(
        "PaymentItemModel",
        back_populates="payment",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        CheckConstraint(
            "amount >= 0",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Payment("
            f"id={self.id}, "
            f"uuid='{self.uuid}', "
            f"status='{self.status.value}'"
            f")>"
        )
