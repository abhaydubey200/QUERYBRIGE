"""Add Phase 2 lineage and governance tables

Revision ID: 004_lineage_governance
Revises: 003_metadata_intelligence
Create Date: 2026-05-12 15:35:36.271000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_lineage_governance'
down_revision = '003_metadata'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create lineage_edges table
    op.create_table(
        'lineage_edges',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('connection_id', sa.String(), nullable=True),
        sa.Column('source_table_id', sa.String(), nullable=True),
        sa.Column('target_table_id', sa.String(), nullable=True),
        sa.Column('source_columns', sa.JSON(), nullable=True),
        sa.Column('target_columns', sa.JSON(), nullable=True),
        sa.Column('lineage_type', sa.String(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('discovery_method', sa.String(), nullable=True),
        sa.Column('transformation_logic', sa.Text(), nullable=True),
        sa.Column('query_template', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('last_verified_at', sa.DateTime(), nullable=True),
        sa.Column('discovered_by', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['connection_id'], ['db_connections.id'], ),
        sa.ForeignKeyConstraint(['source_table_id'], ['catalog_tables.id'], ),
        sa.ForeignKeyConstraint(['target_table_id'], ['catalog_tables.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_lineage_source_target', 'lineage_edges', ['source_table_id', 'target_table_id'], unique=False)
    op.create_index('ix_lineage_connection', 'lineage_edges', ['connection_id'], unique=False)
    op.create_index('ix_lineage_edges_connection_id', 'lineage_edges', ['connection_id'], unique=False)
    
    # Create governance_policies table
    op.create_table(
        'governance_policies',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('workspace_id', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('sensitivity_level', sa.String(), nullable=True),
        sa.Column('contains_pii_condition', sa.Boolean(), nullable=True),
        sa.Column('action_type', sa.String(), nullable=True),
        sa.Column('action_params', sa.JSON(), nullable=True),
        sa.Column('allowed_roles', sa.JSON(), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_governance_workspace', 'governance_policies', ['workspace_id'], unique=False)
    op.create_index('ix_governance_enabled', 'governance_policies', ['enabled'], unique=False)
    op.create_index('ix_governance_policies_name', 'governance_policies', ['name'], unique=False)
    
    # Create audit_logs table (Dropped first to resolve duplication in migration history)
    op.execute("DROP TABLE IF EXISTS audit_logs CASCADE")
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('connection_id', sa.String(), nullable=True),
        sa.Column('workspace_id', sa.String(), nullable=True),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('action', sa.String(), nullable=True),
        sa.Column('resource_type', sa.String(), nullable=True),
        sa.Column('resource_id', sa.String(), nullable=True),
        sa.Column('resource_name', sa.String(), nullable=True),
        sa.Column('query_executed', sa.Text(), nullable=True),
        sa.Column('rows_returned', sa.Integer(), nullable=True),
        sa.Column('rows_masked', sa.Integer(), nullable=True),
        sa.Column('columns_masked', sa.JSON(), nullable=True),
        sa.Column('access_level', sa.String(), nullable=True),
        sa.Column('denial_reason', sa.String(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['connection_id'], ['db_connections.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_user_timestamp', 'audit_logs', ['user_id', 'timestamp'], unique=False)
    op.create_index('ix_audit_resource_id', 'audit_logs', ['resource_id'], unique=False)
    op.create_index('ix_audit_action', 'audit_logs', ['action'], unique=False)
    op.create_index('ix_audit_logs_connection_id', 'audit_logs', ['connection_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_audit_logs_connection_id', table_name='audit_logs')
    op.drop_index('ix_audit_action', table_name='audit_logs')
    op.drop_index('ix_audit_resource_id', table_name='audit_logs')
    op.drop_index('ix_audit_user_timestamp', table_name='audit_logs')
    op.drop_table('audit_logs')
    
    op.drop_index('ix_governance_policies_name', table_name='governance_policies')
    op.drop_index('ix_governance_enabled', table_name='governance_policies')
    op.drop_index('ix_governance_workspace', table_name='governance_policies')
    op.drop_table('governance_policies')
    
    op.drop_index('ix_lineage_edges_connection_id', table_name='lineage_edges')
    op.drop_index('ix_lineage_connection', table_name='lineage_edges')
    op.drop_index('ix_lineage_source_target', table_name='lineage_edges')
    op.drop_table('lineage_edges')
