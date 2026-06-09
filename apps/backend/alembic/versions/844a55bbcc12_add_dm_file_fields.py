"""add_dm_file_fields

Revision ID: 844a55bbcc12
Revises: 733370ddbb11
Create Date: 2026-05-31 22:55:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '844a55bbcc12'
down_revision: Union[str, None] = '733370ddbb11'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('direct_message_rooms', sa.Column('last_message_content', sa.Text(), nullable=True))
    op.add_column('direct_messages', sa.Column('file_name', sa.Text(), nullable=True))
    op.add_column('direct_messages', sa.Column('file_path', sa.Text(), nullable=True))
    op.add_column('direct_messages', sa.Column('file_size', sa.BigInteger(), nullable=True))
    op.add_column('direct_messages', sa.Column('file_type', sa.Text(), nullable=True))
    op.alter_column('direct_messages', 'content', server_default=sa.text("''"), nullable=False)


def downgrade() -> None:
    op.drop_column('direct_messages', 'file_type')
    op.drop_column('direct_messages', 'file_size')
    op.drop_column('direct_messages', 'file_path')
    op.drop_column('direct_messages', 'file_name')
    op.drop_column('direct_message_rooms', 'last_message_content')
    op.alter_column('direct_messages', 'content', server_default=None, nullable=False)
