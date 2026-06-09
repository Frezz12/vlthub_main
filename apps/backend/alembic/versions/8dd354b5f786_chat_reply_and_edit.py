"""chat reply and edit

Revision ID: 8dd354b5f786
Revises: c4ab9a2bcbd7
Create Date: 2026-05-31 01:34:53.234303
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '8dd354b5f786'
down_revision: Union[str, None] = 'c4ab9a2bcbd7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('chat_messages', sa.Column('reply_to_id', sa.UUID(as_uuid=False), nullable=True))
    op.add_column('chat_messages', sa.Column('edited_at', sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key(None, 'chat_messages', 'chat_messages', ['reply_to_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    op.drop_constraint(None, 'chat_messages', type_='foreignkey')
    op.drop_column('chat_messages', 'edited_at')
    op.drop_column('chat_messages', 'reply_to_id')
