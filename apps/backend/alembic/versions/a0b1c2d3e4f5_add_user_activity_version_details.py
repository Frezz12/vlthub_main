"""add version_id and details to user_activities

Revision ID: a0b1c2d3e4f5
Revises: 9f1c2a7b6d10
Create Date: 2026-05-27
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "a0b1c2d3e4f5"
down_revision: Union[str, None] = "9f1c2a7b6d10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_activities",
        sa.Column("version_id", postgresql.UUID(as_uuid=False), nullable=True),
    )
    op.add_column(
        "user_activities",
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.create_foreign_key(
        "fk_user_activities_version_id",
        "user_activities",
        "versions",
        ["version_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_user_activities_project_created",
        "user_activities",
        ["project_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_user_activities_project_created", table_name="user_activities")
    op.drop_constraint("fk_user_activities_version_id", "user_activities", type_="foreignkey")
    op.drop_column("user_activities", "details")
    op.drop_column("user_activities", "version_id")
