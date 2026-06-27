from datetime import datetime

from sqlalchemy import ForeignKey, UniqueConstraint, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models.base import Base


class CartModel(Base):
    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
    )

    user: Mapped["UserModel"] = relationship(
        "UserModel",
        back_populates="cart",
        lazy="selectin",
    )

    items: Mapped[list["CartItemModel"]] = relationship(
        "CartItemModel",
        back_populates="cart",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<Cart("
            f"id={self.id}, "
            f"user_id={self.user_id}"
            f")>"
        )


class CartItemModel(Base):
    __tablename__ = "cart_items"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    cart_id: Mapped[int] = mapped_column(
        ForeignKey(
            "carts.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    movie_id: Mapped[int] = mapped_column(
        ForeignKey(
            "movies.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    cart: Mapped["CartModel"] = relationship(
        "CartModel",
        back_populates="items",
        lazy="selectin",
    )

    movie: Mapped["MovieModel"] = relationship(
        "MovieModel",
        back_populates="cart_items",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint(
            "cart_id",
            "movie_id",
            name="uq_cart_movie",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<CartItem("
            f"cart_id={self.cart_id}, "
            f"movie_id={self.movie_id}"
            f")>"
        )
