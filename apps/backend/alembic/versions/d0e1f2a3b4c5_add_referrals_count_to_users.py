"""Add referrals_count to users

Revision ID: d0e1f2a3b4c5
Revises: c0d1e2f3a4b5
Create Date: 2026-05-30
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "d0e1f2a3b4c5"
down_revision: str | None = "c0d1e2f3a4b5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("referrals_count", sa.Integer(), nullable=False, server_default=sa.text("0")))
    op.alter_column("users", "referrals_count", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "referrals_count")
