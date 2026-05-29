"""add file_path, file_hash, created_at to version_files

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-25 19:20:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("version_files", sa.Column("file_path", sa.String(500), nullable=True))
    op.add_column("version_files", sa.Column("file_hash", sa.String(64), nullable=True))
    op.add_column("version_files", sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()))


def downgrade() -> None:
    op.drop_column("version_files", "created_at")
    op.drop_column("version_files", "file_hash")
    op.drop_column("version_files", "file_path")
