import enum

from sqlalchemy import (
    Enum,
    Integer,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from database.models.base import Base


class UserGroupEnum(str, enum.Enum):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"



class UserGroupModel(Base):
    __tablename__ = "user_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[UserGroupEnum] = mapped_column(Enum(UserGroupEnum), nullable=False, unique=True)

    def __repr__(self):
        return f"<UserGroupModel(id={self.id}, name={self.name})>"
