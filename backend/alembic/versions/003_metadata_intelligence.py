"""Add metadata intelligence tables

Revision ID: 003_metadata
Revises: 002_add_security_infrastructure
Create Date: 2026-05-12 15:20:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '003_metadata'
down_revision: Union[str, None] = '002b_catalog_repair'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # MetadataAsset: Ownership, stewardship, SLA
    op.create_table(
        'metadata_assets',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('table_id', sa.String(), nullable=True),
        sa.Column('owner', sa.String(), nullable=True),
        sa.Column('steward', sa.String(), nullable=True),
        sa.Column('contact_email', sa.String(), nullable=True),
        sa.Column('sla_freshness_hours', sa.Integer(), nullable=True),
        sa.Column('business_owner', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['table_id'], ['catalog_tables.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('table_id')
    )
    op.create_index('ix_metadata_assets_table_id', 'metadata_assets', ['table_id'])

    # MetadataGlossary: Business terms and definitions
    op.create_table(
        'metadata_glossary',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('term', sa.String(), nullable=True),
        sa.Column('definition', sa.Text(), nullable=True),
        sa.Column('domain', sa.String(), nullable=True),
        sa.Column('related_terms', sa.JSON(), nullable=True),
        sa.Column('examples', sa.JSON(), nullable=True),
        sa.Column('owner', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('term')
    )
    op.create_index('ix_metadata_glossary_term', 'metadata_glossary', ['term'])
    op.create_index('ix_metadata_glossary_domain', 'metadata_glossary', ['domain'])

    # MetadataTag: User-applied tags
    op.create_table(
        'metadata_tags',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('table_id', sa.String(), nullable=True),
        sa.Column('column_id', sa.String(), nullable=True),
        sa.Column('tag_type', sa.String(), nullable=True),
        sa.Column('tag_value', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['column_id'], ['catalog_columns.id'], ),
        sa.ForeignKeyConstraint(['table_id'], ['catalog_tables.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_metadata_tags_table_id', 'metadata_tags', ['table_id'])
    op.create_index('ix_metadata_tags_column_id', 'metadata_tags', ['column_id'])
    op.create_index('ix_metadata_tags_tag_type', 'metadata_tags', ['tag_type'])
    op.create_index('ix_metadata_tags_table_type_value', 'metadata_tags', ['table_id', 'tag_type', 'tag_value'])

    # MetadataQualityScore: Data quality metrics
    op.create_table(
        'metadata_quality_scores',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('table_id', sa.String(), nullable=True),
        sa.Column('overall_quality_score', sa.Float(), nullable=True),
        sa.Column('freshness_score', sa.Float(), nullable=True),
        sa.Column('completeness_score', sa.Float(), nullable=True),
        sa.Column('uniqueness_score', sa.Float(), nullable=True),
        sa.Column('accuracy_score', sa.Float(), nullable=True),
        sa.Column('consistency_score', sa.Float(), nullable=True),
        sa.Column('timeliness_score', sa.Float(), nullable=True),
        sa.Column('freshness_hours', sa.Integer(), nullable=True),
        sa.Column('completeness_percent', sa.Float(), nullable=True),
        sa.Column('last_scored_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['table_id'], ['catalog_tables.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_metadata_quality_scores_table_id', 'metadata_quality_scores', ['table_id'])

    # MetadataClassification: Data classification and sensitivity
    op.create_table(
        'metadata_classifications',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('table_id', sa.String(), nullable=True),
        sa.Column('column_id', sa.String(), nullable=True),
        sa.Column('sensitivity_level', sa.String(), nullable=True),
        sa.Column('contains_pii', sa.Boolean(), nullable=True),
        sa.Column('pii_types', sa.JSON(), nullable=True),
        sa.Column('compliance_reqs', sa.JSON(), nullable=True),
        sa.Column('auto_detected', sa.Boolean(), nullable=True),
        sa.Column('detection_confidence', sa.Float(), nullable=True),
        sa.Column('masking_enabled', sa.Boolean(), nullable=True),
        sa.Column('masking_type', sa.String(), nullable=True),
        sa.Column('access_restricted', sa.Boolean(), nullable=True),
        sa.Column('allowed_roles', sa.JSON(), nullable=True),
        sa.Column('classified_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['column_id'], ['catalog_columns.id'], ),
        sa.ForeignKeyConstraint(['table_id'], ['catalog_tables.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_metadata_classifications_table_id', 'metadata_classifications', ['table_id'])
    op.create_index('ix_metadata_classifications_column_id', 'metadata_classifications', ['column_id'])
    op.create_index('ix_metadata_classifications_sensitivity', 'metadata_classifications', ['sensitivity_level'])

    # MetadataCustomField: Extensible custom fields
    op.create_table(
        'metadata_custom_fields',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('table_id', sa.String(), nullable=True),
        sa.Column('column_id', sa.String(), nullable=True),
        sa.Column('field_name', sa.String(), nullable=True),
        sa.Column('field_value', sa.Text(), nullable=True),
        sa.Column('field_type', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['column_id'], ['catalog_columns.id'], ),
        sa.ForeignKeyConstraint(['table_id'], ['catalog_tables.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_metadata_custom_fields_table_id', 'metadata_custom_fields', ['table_id'])
    op.create_index('ix_metadata_custom_fields_column_id', 'metadata_custom_fields', ['column_id'])
    op.create_index('ix_metadata_custom_fields_table_name', 'metadata_custom_fields', ['table_id', 'field_name'])


def downgrade() -> None:
    op.drop_index('ix_metadata_custom_fields_table_name', table_name='metadata_custom_fields')
    op.drop_index('ix_metadata_custom_fields_column_id', table_name='metadata_custom_fields')
    op.drop_index('ix_metadata_custom_fields_table_id', table_name='metadata_custom_fields')
    op.drop_table('metadata_custom_fields')
    
    op.drop_index('ix_metadata_classifications_sensitivity', table_name='metadata_classifications')
    op.drop_index('ix_metadata_classifications_column_id', table_name='metadata_classifications')
    op.drop_index('ix_metadata_classifications_table_id', table_name='metadata_classifications')
    op.drop_table('metadata_classifications')
    
    op.drop_index('ix_metadata_quality_scores_table_id', table_name='metadata_quality_scores')
    op.drop_table('metadata_quality_scores')
    
    op.drop_index('ix_metadata_tags_table_type_value', table_name='metadata_tags')
    op.drop_index('ix_metadata_tags_tag_type', table_name='metadata_tags')
    op.drop_index('ix_metadata_tags_column_id', table_name='metadata_tags')
    op.drop_index('ix_metadata_tags_table_id', table_name='metadata_tags')
    op.drop_table('metadata_tags')
    
    op.drop_index('ix_metadata_glossary_domain', table_name='metadata_glossary')
    op.drop_index('ix_metadata_glossary_term', table_name='metadata_glossary')
    op.drop_table('metadata_glossary')
    
    op.drop_index('ix_metadata_assets_table_id', table_name='metadata_assets')
    op.drop_table('metadata_assets')
