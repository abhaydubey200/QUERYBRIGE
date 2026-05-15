"""Add comprehensive enterprise infrastructure

Revision ID: 002_enterprise_infrastructure
Revises: 001_initial
Create Date: 2026-05-12 14:40:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002_enterprise_infrastructure'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # --- CORE CATALOG TABLES ---
    # 0. Catalog Tables
    op.create_table(
        'catalog_tables',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('connection_id', sa.String(), nullable=True),
        sa.Column('schema_name', sa.String(), nullable=True),
        sa.Column('table_name', sa.String(), nullable=True),
        sa.Column('entity_type', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('row_count_estimate', sa.Integer(), nullable=True),
        sa.Column('size_bytes', sa.Integer(), nullable=True),
        sa.Column('last_metadata_sync', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['connection_id'], ['db_connections.id'], )
    )
    op.create_index('ix_catalog_tables_connection_id', 'catalog_tables', ['connection_id'])
    op.create_index('ix_catalog_tables_schema_name', 'catalog_tables', ['schema_name'])
    op.create_index('ix_catalog_tables_table_name', 'catalog_tables', ['table_name'])

    # 0.1 Catalog Columns
    op.create_table(
        'catalog_columns',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('table_id', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('data_type', sa.String(), nullable=True),
        sa.Column('is_nullable', sa.Boolean(), nullable=True),
        sa.Column('is_primary_key', sa.Boolean(), nullable=True),
        sa.Column('is_foreign_key', sa.Boolean(), nullable=True),
        sa.Column('default_value', sa.String(), nullable=True),
        sa.Column('ordinal_position', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('pii_tag', sa.String(), nullable=True),
        sa.Column('sensitivity_level', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['table_id'], ['catalog_tables.id'], )
    )
    op.create_index('ix_catalog_columns_table_id', 'catalog_columns', ['table_id'])
    op.create_index('ix_catalog_columns_name', 'catalog_columns', ['name'])

    # 0.2 Catalog Relationships
    op.create_table(
        'catalog_relationships',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('connection_id', sa.String(), nullable=True),
        sa.Column('source_table_id', sa.String(), nullable=True),
        sa.Column('source_column_id', sa.String(), nullable=True),
        sa.Column('target_table_id', sa.String(), nullable=True),
        sa.Column('target_column_id', sa.String(), nullable=True),
        sa.Column('relationship_type', sa.String(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('discovery_method', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['connection_id'], ['db_connections.id'], ),
        sa.ForeignKeyConstraint(['source_table_id'], ['catalog_tables.id'], ),
        sa.ForeignKeyConstraint(['source_column_id'], ['catalog_columns.id'], ),
        sa.ForeignKeyConstraint(['target_table_id'], ['catalog_tables.id'], ),
        sa.ForeignKeyConstraint(['target_column_id'], ['catalog_columns.id'], )
    )
    op.create_index('ix_catalog_relationships_connection_id', 'catalog_relationships', ['connection_id'])

    # 0.3 Catalog Profiles
    op.create_table(
        'catalog_profiles',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('table_id', sa.String(), nullable=True),
        sa.Column('column_id', sa.String(), nullable=True),
        sa.Column('distinct_count', sa.Integer(), nullable=True),
        sa.Column('null_count', sa.Integer(), nullable=True),
        sa.Column('min_value', sa.String(), nullable=True),
        sa.Column('max_value', sa.String(), nullable=True),
        sa.Column('avg_value', sa.Float(), nullable=True),
        sa.Column('top_values', sa.JSON(), nullable=True),
        sa.Column('histogram', sa.JSON(), nullable=True),
        sa.Column('cardinality', sa.Float(), nullable=True),
        sa.Column('freshness', sa.DateTime(), nullable=True),
        sa.Column('last_profiled', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['column_id'], ['catalog_columns.id'], ),
        sa.ForeignKeyConstraint(['table_id'], ['catalog_tables.id'], )
    )
    op.create_index('ix_catalog_profiles_column_id', 'catalog_profiles', ['column_id'])
    op.create_index('ix_catalog_profiles_table_id', 'catalog_profiles', ['table_id'])

    # 0.4 Catalog Lineage (Legacy Phase 1)
    op.create_table(
        'catalog_lineage',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('connection_id', sa.String(), nullable=True),
        sa.Column('source_id', sa.String(), nullable=True),
        sa.Column('target_id', sa.String(), nullable=True),
        sa.Column('source_type', sa.String(), nullable=True),
        sa.Column('target_type', sa.String(), nullable=True),
        sa.Column('transformation_logic', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['connection_id'], ['db_connections.id'], )
    )
    op.create_index('ix_catalog_lineage_connection_id', 'catalog_lineage', ['connection_id'])

    # 0.5 Metadata Refresh Jobs
    op.create_table(
        'metadata_refresh_jobs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('connection_id', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('error_log', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['connection_id'], ['db_connections.id'], )
    )
    op.create_index('ix_metadata_refresh_jobs_connection_id', 'metadata_refresh_jobs', ['connection_id'])

    # --- INFRASTRUCTURE TABLES ---
    # 1. SSH Tunnel Configs
    op.create_table(
        'ssh_tunnel_configs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('ssh_host', sa.String(), nullable=True),
        sa.Column('ssh_port', sa.Integer(), nullable=True),
        sa.Column('ssh_user', sa.String(), nullable=True),
        sa.Column('ssh_key_encrypted', sa.Text(), nullable=True),
        sa.Column('ssh_passphrase_encrypted', sa.String(), nullable=True),
        sa.Column('remote_bind_address', sa.String(), nullable=True),
        sa.Column('local_bind_port', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 2. SSL Certificates
    op.create_table(
        'ssl_certificates',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('ca_cert', sa.Text(), nullable=True),
        sa.Column('client_cert', sa.Text(), nullable=True),
        sa.Column('client_key_encrypted', sa.Text(), nullable=True),
        sa.Column('verify_mode', sa.String(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 3. Connection Health Logs
    op.create_table(
        'connection_health_logs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('connection_id', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('latency_ms', sa.Float(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['connection_id'], ['db_connections.id'], )
    )

    # 4. Connection Metrics
    op.create_table(
        'connection_metrics',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('connection_id', sa.String(), nullable=True),
        sa.Column('metric_name', sa.String(), nullable=True),
        sa.Column('value', sa.Float(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['connection_id'], ['db_connections.id'], )
    )

    # 5. AI Conversations
    op.create_table(
        'ai_conversations',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('history', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], )
    )

    # 6. Dashboards
    op.create_table(
        'dashboards',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('config', sa.JSON(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], )
    )

    # 7. Semantic Metrics
    op.create_table(
        'semantic_metrics',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('formula', sa.Text(), nullable=True),
        sa.Column('connection_id', sa.String(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['connection_id'], ['db_connections.id'], )
    )

    # 8. Notebook Sessions
    op.create_table(
        'notebook_sessions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('cells', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], )
    )

    # 9. Catalog Index
    op.create_table(
        'catalog_index',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('connection_id', sa.String(), nullable=True),
        sa.Column('entity_type', sa.String(), nullable=True),
        sa.Column('entity_name', sa.String(), nullable=True),
        sa.Column('entity_description', sa.Text(), nullable=True),
        sa.Column('pii_tags', sa.JSON(), nullable=True),
        sa.Column('last_profiled', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['connection_id'], ['db_connections.id'], )
    )

    # 10. Workspace Members
    op.create_table(
        'workspace_members',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('workspace_id', sa.String(), nullable=True),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('role', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], )
    )

    # Add missing security columns to db_connections
    op.add_column('db_connections', sa.Column('ssl_config_id', sa.String(), nullable=True))
    op.add_column('db_connections', sa.Column('ssh_tunnel_id', sa.String(), nullable=True))
    
    # Add foreign key constraints to db_connections
    op.create_foreign_key('fk_db_connections_ssl_config', 'db_connections', 'ssl_certificates', ['ssl_config_id'], ['id'])
    op.create_foreign_key('fk_db_connections_ssh_tunnel', 'db_connections', 'ssh_tunnel_configs', ['ssh_tunnel_id'], ['id'])

def downgrade() -> None:
    # Drop in reverse order
    op.drop_index('ix_metadata_refresh_jobs_connection_id', table_name='metadata_refresh_jobs')
    op.drop_table('metadata_refresh_jobs')
    
    op.drop_index('ix_catalog_lineage_connection_id', table_name='catalog_lineage')
    op.drop_table('catalog_lineage')
    
    op.drop_index('ix_catalog_profiles_table_id', table_name='catalog_profiles')
    op.drop_index('ix_catalog_profiles_column_id', table_name='catalog_profiles')
    op.drop_table('catalog_profiles')
    
    op.drop_index('ix_catalog_relationships_connection_id', table_name='catalog_relationships')
    op.drop_table('catalog_relationships')
    
    op.drop_index('ix_catalog_columns_name', table_name='catalog_columns')
    op.drop_index('ix_catalog_columns_table_id', table_name='catalog_columns')
    op.drop_table('catalog_columns')
    
    op.drop_index('ix_catalog_tables_table_name', table_name='catalog_tables')
    op.drop_index('ix_catalog_tables_schema_name', table_name='catalog_tables')
    op.drop_index('ix_catalog_tables_connection_id', table_name='catalog_tables')
    op.drop_table('catalog_tables')

    op.drop_table('workspace_members')
    op.drop_table('catalog_index')
    op.drop_table('notebook_sessions')
    op.drop_table('semantic_metrics')
    op.drop_table('dashboards')
    op.drop_table('ai_conversations')
    op.drop_table('connection_metrics')
    op.drop_table('connection_health_logs')
    
    op.drop_constraint('fk_db_connections_ssh_tunnel', 'db_connections', type_='foreignkey')
    op.drop_constraint('fk_db_connections_ssl_config', 'db_connections', type_='foreignkey')
    op.drop_column('db_connections', 'ssh_tunnel_id')
    op.drop_column('db_connections', 'ssl_config_id')
    
    op.drop_table('ssl_certificates')
    op.drop_table('ssh_tunnel_configs')
