"""add code_hash to email_confirmations

Revision ID: 64b96a24c47e
Revises: 0009
Create Date: 2026-05-26 21:31:05.922901
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '64b96a24c47e'
down_revision: Union[str, None] = '0009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('email_confirmations', sa.Column('code_hash', sa.String(255), nullable=False, server_default=''))


def downgrade() -> None:
    op.drop_column('email_confirmations', 'code_hash')
