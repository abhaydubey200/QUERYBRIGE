"""Initial schema

Revision ID: 001_initial
Revises: 
Create Date: 2026-05-11 13:55:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
def upgrade() -> None:
    # Workspaces
    op.create_table(
        'workspaces',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('slug', sa.String(), nullable=True),
        sa.Column('settings', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('slug')
    )
    
    # Users
    op.create_table(
        'users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('hashed_password', sa.String(), nullable=True),
        sa.Column('role', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    
    # DB Connections
    op.create_table(
        'db_connections',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('workspace_id', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('db_type', sa.String(), nullable=True),
        sa.Column('host', sa.String(), nullable=True),
        sa.Column('port', sa.Integer(), nullable=True),
        sa.Column('database', sa.String(), nullable=True),
        sa.Column('username', sa.String(), nullable=True),
        sa.Column('password_encrypted', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('pool_settings', sa.JSON(), nullable=True),
        sa.Column('advanced_settings', sa.JSON(), nullable=True),
        sa.Column('last_heartbeat', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], )
    )
    
    # Audit Logs
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('action', sa.String(), nullable=True),
        sa.Column('resource_id', sa.String(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], )
    )

def downgrade() -> None:
    op.drop_table('audit_logs')
