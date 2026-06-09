"""chat add file fields

Revision ID: c4ab9a2bcbd7
Revises: 299cc80f449d
Create Date: 2026-05-31 01:30:14.742680
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'c4ab9a2bcbd7'
down_revision: Union[str, None] = '299cc80f449d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('chat_messages', sa.Column('file_name', sa.String(length=255), nullable=True))
    op.add_column('chat_messages', sa.Column('file_path', sa.String(length=500), nullable=True))
    op.add_column('chat_messages', sa.Column('file_size', sa.Integer(), nullable=True))
    op.add_column('chat_messages', sa.Column('file_type', sa.String(length=50), nullable=True))
    op.add_column('chat_messages', sa.Column('version_id', sa.UUID(as_uuid=False), nullable=True))
    op.create_foreign_key(None, 'chat_messages', 'versions', ['version_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    op.drop_constraint(None, 'chat_messages', type_='foreignkey')
    op.drop_column('chat_messages', 'version_id')
    op.drop_column('chat_messages', 'file_type')
    op.drop_column('chat_messages', 'file_size')
    op.drop_column('chat_messages', 'file_path')
    op.drop_column('chat_messages', 'file_name')
