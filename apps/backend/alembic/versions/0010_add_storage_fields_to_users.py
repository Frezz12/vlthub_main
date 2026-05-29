"""0010 add is_admin, storage_limit, storage_used to users

Revision ID: 0010
Revises: a0b1c2d3e4f5
Create Date: 2026-05-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0010'
down_revision: Union[str, None] = 'a0b1c2d3e4f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('users', sa.Column('storage_limit', sa.BigInteger(), server_default=sa.text('5368709120'), nullable=False))
    op.add_column('users', sa.Column('storage_used', sa.BigInteger(), server_default=sa.text('0'), nullable=False))


def downgrade() -> None:
    op.drop_column('users', 'storage_used')
    op.drop_column('users', 'storage_limit')
    op.drop_column('users', 'is_admin')
