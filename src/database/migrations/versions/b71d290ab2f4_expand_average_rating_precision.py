"""Allow an average rating of 10.00.

Revision ID: b71d290ab2f4
Revises: 5c2f0d6edb0c
Create Date: 2026-09-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b71d290ab2f4"
down_revision: Union[str, Sequence[str], None] = "5c2f0d6edb0c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "movies",
        "average_rating",
        existing_type=sa.Numeric(precision=3, scale=2),
        type_=sa.Numeric(precision=4, scale=2),
        existing_nullable=False,
        existing_server_default="0",
    )


def downgrade() -> None:
    op.alter_column(
        "movies",
        "average_rating",
        existing_type=sa.Numeric(precision=4, scale=2),
        type_=sa.Numeric(precision=3, scale=2),
        existing_nullable=False,
        existing_server_default="0",
    )
