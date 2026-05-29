"""0006_add_beatmaker_status_follow_tasks

Revision ID: 1dec5f0c1b50
Revises: 0005
Create Date: 2026-05-26 19:00:34.355004
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '1dec5f0c1b50'
down_revision: Union[str, None] = '0005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Projects: add beatmaker, status; drop sample_rate
    op.add_column('projects', sa.Column('beatmaker', sa.String(200), nullable=True))
    op.add_column('projects', sa.Column('status', sa.String(20), nullable=False, server_default='in_progress'))
    op.drop_column('projects', 'sample_rate')

    # Notifications: add related_user_id
    op.add_column('notifications', sa.Column('related_user_id', postgresql.UUID(as_uuid=False), nullable=True))

    # Follows table
    op.create_table('follows',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True, nullable=False),
        sa.Column('follower_id', postgresql.UUID(as_uuid=False), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('following_id', postgresql.UUID(as_uuid=False), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.UniqueConstraint('follower_id', 'following_id', name='uq_follows'),
    )

    # Version tasks table
    op.create_table('version_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True, nullable=False),
        sa.Column('version_id', postgresql.UUID(as_uuid=False), sa.ForeignKey('versions.id'), nullable=False),
        sa.Column('text', sa.String(500), nullable=False),
        sa.Column('is_done', sa.Boolean(), default=False, nullable=True),
        sa.Column('position', sa.Integer(), default=0, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
    )

    # Drop project_external_artists
    op.drop_table('project_external_artists')


def downgrade() -> None:
    # Re-create project_external_artists
    op.create_table('project_external_artists',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True, nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=False), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('role', sa.String(100), nullable=False),
    )

    # Drop version_tasks
    op.drop_table('version_tasks')

    # Drop follows
    op.drop_table('follows')

    # Remove related_user_id from notifications
    op.drop_column('notifications', 'related_user_id')

    # Restore sample_rate, drop beatmaker and status
    op.add_column('projects', sa.Column('sample_rate', sa.Integer(), nullable=True))
    op.drop_column('projects', 'status')
    op.drop_column('projects', 'beatmaker')
