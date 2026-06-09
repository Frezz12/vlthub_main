"""add deleted_by to chat_messages for self-delete

Revision ID: e0f1a2b3c4d5
Revises: 8dd354b5f786
Create Date: 2026-05-31 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'e0f1a2b3c4d5'
down_revision: Union[str, None] = '8dd354b5f786'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('chat_messages', sa.Column('deleted_by', postgresql.JSON, nullable=True))


def downgrade() -> None:
    op.drop_column('chat_messages', 'deleted_by')
