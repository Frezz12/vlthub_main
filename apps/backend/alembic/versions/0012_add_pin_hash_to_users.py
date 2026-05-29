"""Add pin_hash column to users table

Revision ID: 0012
Revises: 0011
Create Date: 2026-05-28
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("pin_hash", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "pin_hash")
