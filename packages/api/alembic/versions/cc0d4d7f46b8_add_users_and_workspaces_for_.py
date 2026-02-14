"""Add users and workspaces for multitenancy

Revision ID: cc0d4d7f46b8
Revises: a3b7c1d2e4f5
Create Date: 2026-02-14 17:31:41.980171

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'cc0d4d7f46b8'
down_revision: str | Sequence[str] | None = 'a3b7c1d2e4f5'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # users 테이블
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(320), unique=True, nullable=False, index=True),
        sa.Column('name', sa.String(200), nullable=True),
        sa.Column('image', sa.String(500), nullable=True),
        sa.Column('provider', sa.String(20), nullable=False, server_default='email'),
        sa.Column('provider_account_id', sa.String(200), nullable=True),
        sa.Column('plan', sa.String(20), nullable=False, server_default='free'),
        sa.Column('is_active', sa.Boolean(), server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )

    # workspaces 테이블
    op.create_table(
        'workspaces',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('owner_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('plan', sa.String(20), nullable=False, server_default='free'),
        sa.Column('pipeline_quota', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('channel_quota', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )

    # 기존 테이블에 workspace_id FK 추가
    with op.batch_alter_table('pipeline_runs') as batch_op:
        batch_op.add_column(sa.Column('workspace_id', sa.String(36), nullable=True))
        batch_op.create_index('ix_pipeline_runs_workspace_id', ['workspace_id'])
        batch_op.create_foreign_key(
            'fk_pipeline_runs_workspace_id',
            'workspaces',
            ['workspace_id'],
            ['id'],
            ondelete='SET NULL',
        )

    with op.batch_alter_table('api_keys') as batch_op:
        batch_op.add_column(sa.Column('workspace_id', sa.String(36), nullable=True))
        batch_op.create_index('ix_api_keys_workspace_id', ['workspace_id'])
        batch_op.create_foreign_key(
            'fk_api_keys_workspace_id',
            'workspaces',
            ['workspace_id'],
            ['id'],
            ondelete='SET NULL',
        )

    with op.batch_alter_table('audit_logs') as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.String(36), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('audit_logs') as batch_op:
        batch_op.drop_column('user_id')

    with op.batch_alter_table('api_keys') as batch_op:
        batch_op.drop_constraint('fk_api_keys_workspace_id', type_='foreignkey')
        batch_op.drop_index('ix_api_keys_workspace_id')
        batch_op.drop_column('workspace_id')

    with op.batch_alter_table('pipeline_runs') as batch_op:
        batch_op.drop_constraint('fk_pipeline_runs_workspace_id', type_='foreignkey')
        batch_op.drop_index('ix_pipeline_runs_workspace_id')
        batch_op.drop_column('workspace_id')

    op.drop_table('workspaces')
    op.drop_table('users')
