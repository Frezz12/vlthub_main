"""add ondelete cascade to project_user_paths and project_access_requests

Revision ID: b0c1d2e3f4a5
Revises: f0a1b2c3d4e5
Create Date: 2026-05-30 05:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b0c1d2e3f4a5"
down_revision: str | None = "f0a1b2c3d4e5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("project_user_paths_project_id_fkey", "project_user_paths", type_="foreignkey")
    op.create_foreign_key(
        "project_user_paths_project_id_fkey",
        "project_user_paths",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint(
        "project_access_requests_project_id_fkey",
        "project_access_requests",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "project_access_requests_project_id_fkey",
        "project_access_requests",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("project_user_paths_project_id_fkey", "project_user_paths", type_="foreignkey")
    op.create_foreign_key(
        "project_user_paths_project_id_fkey",
        "project_user_paths",
        "projects",
        ["project_id"],
        ["id"],
    )
    op.drop_constraint(
        "project_access_requests_project_id_fkey",
        "project_access_requests",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "project_access_requests_project_id_fkey",
        "project_access_requests",
        "projects",
        ["project_id"],
        ["id"],
    )
