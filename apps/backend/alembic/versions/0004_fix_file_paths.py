"""Fix version file_path to be relative to uploads directory.

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-25
"""
from typing import Sequence

from alembic import op
from sqlalchemy import text

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()
    for table in ("versions", "version_files"):
        conn.execute(
            text(
                f"UPDATE {table} SET file_path = substr(file_path, 9) "
                f"WHERE file_path LIKE 'uploads/%'"
            )
        )


def downgrade() -> None:
    pass

