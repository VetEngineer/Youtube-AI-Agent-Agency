"""add workspace_id to audit_logs

Revision ID: 448054d4793a
Revises: 60356f47bda7
Create Date: 2026-04-09 00:50:52.472397

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '448054d4793a'
down_revision: str | Sequence[str] | None = '60356f47bda7'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('audit_logs', sa.Column('workspace_id', sa.String(length=36), nullable=True))
    op.create_index(op.f('ix_audit_logs_workspace_id'), 'audit_logs', ['workspace_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_audit_logs_workspace_id'), table_name='audit_logs')
    op.drop_column('audit_logs', 'workspace_id')
