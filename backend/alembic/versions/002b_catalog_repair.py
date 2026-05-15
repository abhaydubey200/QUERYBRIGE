"""Repair missing catalog tables

Revision ID: 002b_catalog_repair
Revises: 002_enterprise_infrastructure
Create Date: 2026-05-13 14:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002b_catalog_repair'
down_revision: Union[str, None] = '002_enterprise_infrastructure'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Use raw SQL with IF NOT EXISTS to ensure this succeeds even if some tables were partially created
    
    # 1. Catalog Tables
    op.execute("""
        CREATE TABLE IF NOT EXISTS catalog_tables (
            id VARCHAR NOT NULL,
            connection_id VARCHAR,
            schema_name VARCHAR,
            table_name VARCHAR,
            entity_type VARCHAR,
            description TEXT,
            row_count_estimate INTEGER,
            size_bytes INTEGER,
            last_metadata_sync TIMESTAMP WITHOUT TIME ZONE,
            PRIMARY KEY (id),
            FOREIGN KEY(connection_id) REFERENCES db_connections (id)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_catalog_tables_connection_id ON catalog_tables (connection_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_catalog_tables_schema_name ON catalog_tables (schema_name)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_catalog_tables_table_name ON catalog_tables (table_name)")

    # 2. Catalog Columns
    op.execute("""
        CREATE TABLE IF NOT EXISTS catalog_columns (
            id VARCHAR NOT NULL,
            table_id VARCHAR,
            name VARCHAR,
            data_type VARCHAR,
            is_nullable BOOLEAN,
            is_primary_key BOOLEAN,
            is_foreign_key BOOLEAN,
            default_value VARCHAR,
            ordinal_position INTEGER,
            description TEXT,
            pii_tag VARCHAR,
            sensitivity_level VARCHAR,
            PRIMARY KEY (id),
            FOREIGN KEY(table_id) REFERENCES catalog_tables (id)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_catalog_columns_table_id ON catalog_columns (table_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_catalog_columns_name ON catalog_columns (name)")

    # 3. Catalog Relationships
    op.execute("""
        CREATE TABLE IF NOT EXISTS catalog_relationships (
            id VARCHAR NOT NULL,
            connection_id VARCHAR,
            source_table_id VARCHAR,
            source_column_id VARCHAR,
            target_table_id VARCHAR,
            target_column_id VARCHAR,
            relationship_type VARCHAR,
            confidence_score FLOAT,
            discovery_method VARCHAR,
            PRIMARY KEY (id),
            FOREIGN KEY(connection_id) REFERENCES db_connections (id),
            FOREIGN KEY(source_table_id) REFERENCES catalog_tables (id),
            FOREIGN KEY(source_column_id) REFERENCES catalog_columns (id),
            FOREIGN KEY(target_table_id) REFERENCES catalog_tables (id),
            FOREIGN KEY(target_column_id) REFERENCES catalog_columns (id)
        )
    """)

    # 4. Catalog Profiles
    op.execute("""
        CREATE TABLE IF NOT EXISTS catalog_profiles (
            id VARCHAR NOT NULL,
            table_id VARCHAR,
            column_id VARCHAR,
            distinct_count INTEGER,
            null_count INTEGER,
            min_value VARCHAR,
            max_value VARCHAR,
            avg_value FLOAT,
            top_values JSON,
            histogram JSON,
            cardinality FLOAT,
            freshness TIMESTAMP WITHOUT TIME ZONE,
            last_profiled TIMESTAMP WITHOUT TIME ZONE,
            PRIMARY KEY (id),
            FOREIGN KEY(column_id) REFERENCES catalog_columns (id),
            FOREIGN KEY(table_id) REFERENCES catalog_tables (id)
        )
    """)

    # 5. Metadata Refresh Jobs
    op.execute("""
        CREATE TABLE IF NOT EXISTS metadata_refresh_jobs (
            id VARCHAR NOT NULL,
            connection_id VARCHAR,
            status VARCHAR,
            started_at TIMESTAMP WITHOUT TIME ZONE,
            finished_at TIMESTAMP WITHOUT TIME ZONE,
            error_log TEXT,
            PRIMARY KEY (id),
            FOREIGN KEY(connection_id) REFERENCES db_connections (id)
        )
    """)

def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS metadata_refresh_jobs CASCADE")
    op.execute("DROP TABLE IF EXISTS catalog_profiles CASCADE")
    op.execute("DROP TABLE IF EXISTS catalog_relationships CASCADE")
    op.execute("DROP TABLE IF EXISTS catalog_columns CASCADE")
    op.execute("DROP TABLE IF EXISTS catalog_tables CASCADE")
