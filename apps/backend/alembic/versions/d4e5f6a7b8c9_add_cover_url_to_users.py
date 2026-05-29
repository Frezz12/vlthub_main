"""add cover_url to users

Revision ID: d4e5f6a7b8c9
Revises: 38e7f1a2b3c4
Create Date: 2026-05-29 02:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = '38e7f1a2b3c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('users')]
    if 'cover_url' not in columns:
        op.add_column('users', sa.Column('cover_url', sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'cover_url')
