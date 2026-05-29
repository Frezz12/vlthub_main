"""add avatar_ring_gradient and avatar_ring_effect to badges

Revision ID: d1e2f3a4b5c6
Revises: d4e5f6a7b8c9
Create Date: 2026-05-29 03:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d1e2f3a4b5c6"
down_revision: str | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("badges", sa.Column("avatar_ring_gradient", sa.Text(), nullable=True))
    op.add_column("badges", sa.Column("avatar_ring_effect", sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column("badges", "avatar_ring_effect")
    op.drop_column("badges", "avatar_ring_gradient")
