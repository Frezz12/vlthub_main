"""add_room_deleted_by

Revision ID: f1a2b3c4d5e6
Revises: 844a55bbcc12
Create Date: 2026-05-31 23:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = '844a55bbcc12'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('direct_message_rooms', sa.Column('deleted_by', postgresql.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('direct_message_rooms', 'deleted_by')
