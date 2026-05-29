"""add artists and sample_rate to projects

Revision ID: 9f1c2a7b6d10
Revises: 64b96a24c47e
Create Date: 2026-05-27
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9f1c2a7b6d10"
down_revision: Union[str, None] = "64b96a24c47e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("artists", sa.String(length=500), nullable=True))
    op.add_column("projects", sa.Column("sample_rate", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("projects", "sample_rate")
    op.drop_column("projects", "artists")
