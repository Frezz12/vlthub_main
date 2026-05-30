"""Add referral_code and referred_by to users

Revision ID: c0d1e2f3a4b5
Revises: b0c1d2e3f4a5
Create Date: 2026-05-30
"""

import secrets
import string
from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "c0d1e2f3a4b5"
down_revision: str | None = "b0c1d2e3f4a5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _generate_code() -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "VLT" + "".join(secrets.choice(alphabet) for _ in range(6))


def upgrade() -> None:
    op.add_column("users", sa.Column("referral_code", sa.String(20), nullable=True))
    op.add_column("users", sa.Column("referred_by", sa.String(20), nullable=True))

    connection = op.get_bind()
    users = connection.execute(sa.text("SELECT id FROM users")).fetchall()
    used_codes: set[str] = set()
    for (uid,) in users:
        while True:
            code = _generate_code()
            if code not in used_codes:
                used_codes.add(code)
                break
        connection.execute(
            sa.text("UPDATE users SET referral_code = :code WHERE id = :id"),
            {"code": code, "id": uid},
        )

    op.alter_column("users", "referral_code", nullable=False)
    op.create_index("ix_users_referral_code", "users", ["referral_code"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_referral_code")
    op.drop_column("users", "referred_by")
    op.drop_column("users", "referral_code")
