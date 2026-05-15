from sqlalchemy import Column, String, Boolean, DateTime, JSON, ForeignKey, Integer, Text, Float
from sqlalchemy.orm import relationship
from app.db.session import Base
import datetime
import uuid

class CatalogTable(Base):
    __tablename__ = "catalog_tables"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    connection_id = Column(String, ForeignKey("db_connections.id"), index=True)
    schema_name = Column(String, index=True)
    table_name = Column(String, index=True)
    entity_type = Column(String)  # table, view, materialized_view
    description = Column(Text)
    row_count_estimate = Column(Integer)
    size_bytes = Column(Integer)
    last_metadata_sync = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    columns = relationship("CatalogColumn", back_populates="table", cascade="all, delete-orphan")
    profiles = relationship("CatalogProfile", back_populates="table", cascade="all, delete-orphan")

class CatalogColumn(Base):
    __tablename__ = "catalog_columns"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    table_id = Column(String, ForeignKey("catalog_tables.id"), index=True)
    name = Column(String, index=True)
    data_type = Column(String)
    is_nullable = Column(Boolean, default=True)
    is_primary_key = Column(Boolean, default=False)
    is_foreign_key = Column(Boolean, default=False)
    default_value = Column(String)
    ordinal_position = Column(Integer)
    description = Column(Text)
    pii_tag = Column(String)  # email, phone, ssn, etc.
    sensitivity_level = Column(String)  # public, internal, confidential, restricted

    # Relationships
    table = relationship("CatalogTable", back_populates="columns")

class CatalogRelationship(Base):
    __tablename__ = "catalog_relationships"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    connection_id = Column(String, ForeignKey("db_connections.id"), index=True)
    source_table_id = Column(String, ForeignKey("catalog_tables.id"))
    source_column_id = Column(String, ForeignKey("catalog_columns.id"))
    target_table_id = Column(String, ForeignKey("catalog_tables.id"))
    target_column_id = Column(String, ForeignKey("catalog_columns.id"))
    relationship_type = Column(String)  # One-to-One, One-to-Many, Many-to-Many
    confidence_score = Column(Float)
    discovery_method = Column(String)  # inferred, explicit (from DB constraints)

class CatalogProfile(Base):
    __tablename__ = "catalog_profiles"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    table_id = Column(String, ForeignKey("catalog_tables.id"), index=True)
    column_id = Column(String, ForeignKey("catalog_columns.id"), index=True)
    distinct_count = Column(Integer)
    null_count = Column(Integer)
    min_value = Column(String)
    max_value = Column(String)
    avg_value = Column(Float)
    top_values = Column(JSON)  # [{value: x, count: y}]
    histogram = Column(JSON)
    cardinality = Column(Float)
    freshness = Column(DateTime)
    last_profiled = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    table = relationship("CatalogTable", back_populates="profiles")

class CatalogLineage(Base):
    __tablename__ = "catalog_lineage"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    connection_id = Column(String, ForeignKey("db_connections.id"), index=True)
    source_id = Column(String)  # ID of source table/column/metric
    target_id = Column(String)  # ID of target table/column/metric
    source_type = Column(String)
    target_type = Column(String)
    transformation_logic = Column(Text)

class MetadataRefreshJob(Base):
    __tablename__ = "metadata_refresh_jobs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    connection_id = Column(String, ForeignKey("db_connections.id"), index=True)
    status = Column(String)  # pending, running, completed, failed
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    error_log = Column(Text)


# ======================== METADATA ENHANCEMENT MODELS ========================

class MetadataAsset(Base):
    """Asset metadata: ownership, stewardship, SLA"""
    __tablename__ = "metadata_assets"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    table_id = Column(String, ForeignKey("catalog_tables.id"), unique=True, index=True)
    owner = Column(String)  # Owner name/email
    steward = Column(String)  # Data steward
    contact_email = Column(String)  # Point of contact
    sla_freshness_hours = Column(Integer)  # Expected freshness SLA
    business_owner = Column(String)  # Business-side owner
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    table = relationship("CatalogTable", backref="asset")


class MetadataGlossary(Base):
    """Business glossary for semantic understanding"""
    __tablename__ = "metadata_glossary"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    term = Column(String, unique=True, index=True)  # Business term (e.g., "Customer")
    definition = Column(Text)  # Clear definition
    domain = Column(String, index=True)  # Business domain (Finance, HR, Sales, etc.)
    related_terms = Column(JSON, default=list)  # [term1, term2, ...]
    examples = Column(JSON, default=list)  # [example1, example2, ...]
    owner = Column(String)  # Who maintains this definition
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class MetadataTag(Base):
    """User-applied tags for categorization"""
    __tablename__ = "metadata_tags"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    table_id = Column(String, ForeignKey("catalog_tables.id"), index=True)
    column_id = Column(String, ForeignKey("catalog_columns.id"), index=True)
    tag_type = Column(String, index=True)  # domain, product, sensitivity, owner_team, etc.
    tag_value = Column(String, index=True)  # Actual tag value
    created_by = Column(String)  # User who applied the tag
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Composite index for efficient queries
    __table_args__ = (
        __import__('sqlalchemy').Index('ix_metadata_tags_table_type_value', 'table_id', 'tag_type', 'tag_value'),
    )


class MetadataQualityScore(Base):
    """Data quality metrics and scores"""
    __tablename__ = "metadata_quality_scores"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    table_id = Column(String, ForeignKey("catalog_tables.id"), index=True)
    
    # Overall quality score (0-100)
    overall_quality_score = Column(Float, default=0.0)
    
    # Quality dimensions (0-100 each)
    freshness_score = Column(Float, default=0.0)  # How recent is the data?
    completeness_score = Column(Float, default=0.0)  # Non-null %
    uniqueness_score = Column(Float, default=0.0)  # PK uniqueness
    accuracy_score = Column(Float, default=0.0)  # Plausibility checks
    consistency_score = Column(Float, default=0.0)  # Cross-table consistency
    timeliness_score = Column(Float, default=0.0)  # Update frequency vs. SLA
    
    # Supporting metrics
    freshness_hours = Column(Integer)  # Hours since last update
    completeness_percent = Column(Float)  # % of non-null rows
    last_scored_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    table = relationship("CatalogTable", backref="quality_score")


class MetadataClassification(Base):
    """Data classification and sensitivity levels"""
    __tablename__ = "metadata_classifications"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    table_id = Column(String, ForeignKey("catalog_tables.id"), index=True)
    column_id = Column(String, ForeignKey("catalog_columns.id"), index=True)
    
    # Classification levels
    sensitivity_level = Column(String, index=True)  # public, internal, confidential, restricted
    contains_pii = Column(Boolean, default=False)
    pii_types = Column(JSON, default=list)  # [email, phone, ssn, ...]
    compliance_reqs = Column(JSON, default=list)  # [GDPR, HIPAA, CCPA, ...]
    
    # Auto-detected vs. manually set
    auto_detected = Column(Boolean, default=False)
    detection_confidence = Column(Float, default=0.0)  # 0-1 confidence score
    
    # Masking & policy application
    masking_enabled = Column(Boolean, default=False)
    masking_type = Column(String)  # none, hash, partial, token, etc.
    access_restricted = Column(Boolean, default=False)
    allowed_roles = Column(JSON, default=list)  # Roles allowed to access
    
    classified_by = Column(String)  # User or system
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class MetadataCustomField(Base):
    """Extensible custom metadata fields"""
    __tablename__ = "metadata_custom_fields"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    table_id = Column(String, ForeignKey("catalog_tables.id"), index=True)
    column_id = Column(String, ForeignKey("catalog_columns.id"), index=True)
    
    field_name = Column(String, index=True)  # Custom field name
    field_value = Column(Text)  # Custom value (JSON string for complex types)
    field_type = Column(String)  # string, json, number, boolean, date
    
    created_by = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    __table_args__ = (
        __import__('sqlalchemy').Index('ix_metadata_custom_fields_table_name', 'table_id', 'field_name'),
    )


# ============ PHASE 2: LINEAGE & GOVERNANCE MODELS ============

class LineageEdge(Base):
    """Represents a data lineage dependency between tables"""
    __tablename__ = "lineage_edges"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    connection_id = Column(String, ForeignKey("db_connections.id"), index=True)
    
    # Source and target tables
    source_table_id = Column(String, ForeignKey("catalog_tables.id"), index=True)
    target_table_id = Column(String, ForeignKey("catalog_tables.id"), index=True)
    
    # Column-level lineage
    source_columns = Column(JSON)  # List of source column IDs: ["col_1", "col_2"]
    target_columns = Column(JSON)  # List of target column IDs: ["col_3"]
    
    # Lineage metadata
    lineage_type = Column(String)  # 'direct' (FK), 'join', 'transform', 'union', 'aggregate'
    confidence = Column(Float, default=0.5)  # 0-1 confidence score
    discovery_method = Column(String)  # 'sql_parser', 'fk_constraint', 'procedure_analysis', 'manual'
    
    # Transformation details
    transformation_logic = Column(Text)  # Description of what happens (e.g., "SUM(amount)")
    query_template = Column(Text)  # Sample SQL or transformation pattern
    
    # Tracking
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_verified_at = Column(DateTime)
    discovered_by = Column(String)  # User or service that created lineage
    
    # Relationships
    source_table = relationship("CatalogTable", foreign_keys=[source_table_id])
    target_table = relationship("CatalogTable", foreign_keys=[target_table_id])
    
    __table_args__ = (
        __import__('sqlalchemy').Index('ix_lineage_source_target', 'source_table_id', 'target_table_id'),
        __import__('sqlalchemy').Index('ix_lineage_connection', 'connection_id'),
    )


class GovernancePolicy(Base):
    """Represents a governance rule to be applied based on classification"""
    __tablename__ = "governance_policies"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String, index=True)  # Multi-tenancy support
    
    # Policy identification
    name = Column(String, index=True)  # e.g., "Mask PII Columns"
    description = Column(Text)
    
    # Trigger conditions
    sensitivity_level = Column(String)  # public, internal, confidential, restricted (or NULL for any)
    contains_pii_condition = Column(Boolean)  # Apply if PII detected? (or NULL for ignore)
    
    # Action to take
    action_type = Column(String)  # 'mask', 'restrict_access', 'audit_only', 'encrypt', 'tag'
    action_params = Column(JSON)  # Varies by action type
    # Example for masking:
    # {
    #     "mask_type": "email",  # email, ssn, credit_card, custom
    #     "mask_pattern": "***@domain.com",
    #     "show_first_chars": 3,
    #     "show_last_chars": 4
    # }
    
    # Authorization
    allowed_roles = Column(JSON)  # List of roles that can bypass: ["admin", "data_team"]
    enabled = Column(Boolean, default=True)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    created_by = Column(String)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    __table_args__ = (
        __import__('sqlalchemy').Index('ix_governance_workspace', 'workspace_id'),
        __import__('sqlalchemy').Index('ix_governance_enabled', 'enabled'),
    )


class AuditLog(Base):
    """Tracks all data access and governance action for compliance"""
    __tablename__ = "audit_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    connection_id = Column(String, ForeignKey("db_connections.id"), index=True)
    workspace_id = Column(String, index=True)
    
    # User & Action
    user_id = Column(String, index=True)  # User who performed action
    action = Column(String, index=True)  # 'query_executed', 'metadata_accessed', 'data_masked', 'access_denied'
    
    # Resource being accessed
    resource_type = Column(String)  # 'table', 'column', 'view', 'procedure'
    resource_id = Column(String, index=True)  # ID of resource accessed
    resource_name = Column(String)  # Name for easy reading
    
    # Query details
    query_executed = Column(Text)  # SQL query if applicable
    rows_returned = Column(Integer)  # Number of rows in result
    rows_masked = Column(Integer)  # Number of values masked
    columns_masked = Column(JSON)  # List of column names masked
    
    # Access control
    access_level = Column(String)  # 'full', 'masked', 'denied'
    denial_reason = Column(String)  # If access denied, why?
    
    # Network & security
    ip_address = Column(String)
    user_agent = Column(String)
    
    # Timing
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    execution_time_ms = Column(Integer)  # Query execution time
    
    # Extensibility
    metadata_ = Column("metadata", JSON, default=dict) # JSON metadata
    
    __table_args__ = (
        __import__('sqlalchemy').Index('ix_audit_user_timestamp', 'user_id', 'timestamp'),
        __import__('sqlalchemy').Index('ix_audit_resource_id', 'resource_id'),
        __import__('sqlalchemy').Index('ix_audit_action', 'action'),
    )
