"""Add settings JSONB column to users table.

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-25
"""
from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("settings", postgresql.JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column("users", "settings")

