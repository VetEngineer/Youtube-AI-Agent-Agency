"""Add youtube_api_key to workspaces for per-workspace YouTube Data API key storage

Revision ID: a1b2c3d4e5f6
Revises: f6a7b8c9d0e1
Create Date: 2026-03-20 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "f6a7b8c9d0e1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "workspaces",
        sa.Column("youtube_api_key", sa.String(length=200), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("workspaces", "youtube_api_key")
