"""0009 add telegram_id and telegram_username to users

Revision ID: 0009
Revises: 0008
Create Date: 2026-05-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0009'
down_revision: Union[str, None] = '0008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('telegram_id', sa.String(100), unique=True, nullable=True))
    op.add_column('users', sa.Column('telegram_username', sa.String(100), nullable=True))
    op.create_index('ix_users_telegram_id', 'users', ['telegram_id'])


def downgrade() -> None:
    op.drop_index('ix_users_telegram_id', table_name='users')
    op.drop_column('users', 'telegram_username')
    op.drop_column('users', 'telegram_id')
