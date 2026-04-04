"""add elevenlabs_api_key to workspaces

Revision ID: 60356f47bda7
Revises: b2c3d4e5f6a7
Create Date: 2026-04-05 00:44:34.732944

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "60356f47bda7"
down_revision: str | Sequence[str] | None = "b2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "workspaces", sa.Column("elevenlabs_api_key", sa.String(length=200), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("workspaces", "elevenlabs_api_key")
