"""add_is_admin_to_users

Revision ID: 4fc5d0137cdd
Revises: 448054d4793a
Create Date: 2026-04-10 16:22:08.820218

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '4fc5d0137cdd'
down_revision: str | Sequence[str] | None = '448054d4793a'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'is_admin')
