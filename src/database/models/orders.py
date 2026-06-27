from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import uuid4

from sqlalchemy import (
    Enum as SQLEnum,
    ForeignKey,
    Numeric,
    String,
    CheckConstraint,
    DateTime,
    func,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from src.database.models.base import Base
from src.database.models.payments import PaymentModel, PaymentItemModel


class OrderStatusEnum(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    CANCELED = "canceled"


class OrderModel(Base):
    __tablename__ = "orders"

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

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    status: Mapped[OrderStatusEnum] = mapped_column(
        SQLEnum(
            OrderStatusEnum,
            name="order_status_enum",
        ),
        default=OrderStatusEnum.PENDING,
        nullable=False,
    )

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=0,
    )

    user: Mapped["UserModel"] = relationship(
        "UserModel",
        back_populates="orders",
        lazy="selectin",
    )

    items: Mapped[list["OrderItemModel"]] = relationship(
        "OrderItemModel",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    payments: Mapped[list["PaymentModel"]] = relationship(
        "PaymentModel",
        back_populates="order",
        lazy="selectin",
    )

    __table_args__ = (
        CheckConstraint(
            "total_amount >= 0",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Order("
            f"id={self.id}, "
            f"uuid='{self.uuid}', "
            f"status='{self.status.value}'"
            f")>"
        )


class OrderItemModel(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    order_id: Mapped[int] = mapped_column(
        ForeignKey(
            "orders.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    movie_id: Mapped[int] = mapped_column(
        ForeignKey(
            "movies.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    price_at_order: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    order: Mapped["OrderModel"] = relationship(
        "OrderModel",
        back_populates="items",
        lazy="selectin",
    )

    movie: Mapped["MovieModel"] = relationship(
        "MovieModel",
        back_populates="order_items",
        lazy="selectin",
    )

    payment_items: Mapped[list["PaymentItemModel"]] = relationship(
        "PaymentItemModel",
        back_populates="order_item",
        lazy="selectin",
    )

    __table_args__ = (
        CheckConstraint(
            "price_at_order >= 0",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<OrderItem("
            f"id={self.id}, "
            f"order_id={self.order_id}, "
            f"movie_id={self.movie_id}"
            f")>"
        )
