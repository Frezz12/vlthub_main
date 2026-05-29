"""add_badges_system

Revision ID: 38e7f1a2b3c4
Revises: a1b2c3d4e5f6
Create Date: 2026-05-29 01:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = '38e7f1a2b3c4'
down_revision: Union[str, None] = '0012'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'badges',
        sa.Column('id', UUID(as_uuid=False), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('icon_svg', sa.Text(), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        'user_badges',
        sa.Column('id', UUID(as_uuid=False), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=False), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('badge_id', UUID(as_uuid=False), sa.ForeignKey('badges.id'), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=False),
        sa.UniqueConstraint('user_id', 'badge_id', name='uq_user_badge'),
    )


def downgrade() -> None:
    op.drop_table('user_badges')
    op.drop_table('badges')
