"""add_direct_messages

Revision ID: 733370ddbb11
Revises: e91b1b1de9e6
Create Date: 2026-05-31 22:50:18.425033
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '733370ddbb11'
down_revision: Union[str, None] = 'e91b1b1de9e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('direct_message_rooms',
    sa.Column('id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('user1_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('user2_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('last_message_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user1_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['user2_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('direct_messages',
    sa.Column('id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('room_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('sender_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('reply_to_id', sa.UUID(as_uuid=False), nullable=True),
    sa.Column('edited_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('deleted_by', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('reactions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['reply_to_id'], ['direct_messages.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['room_id'], ['direct_message_rooms.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('direct_messages')
    op.drop_table('direct_message_rooms')
