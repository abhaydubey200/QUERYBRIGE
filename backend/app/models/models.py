from sqlalchemy import Column, String, Boolean, DateTime, JSON, ForeignKey, Integer, Text, Float
from sqlalchemy.orm import relationship
from app.db.session import Base
import datetime
import uuid
from app.models.catalog_models import (
    CatalogTable, CatalogColumn, CatalogRelationship, 
    CatalogProfile, CatalogLineage, MetadataRefreshJob,
    AuditLog
)

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="viewer")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class DBConnection(Base):
    __tablename__ = "db_connections"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String, ForeignKey("workspaces.id"), index=True)
    name = Column(String, index=True)
    db_type = Column(String)
    host = Column(String)
    port = Column(Integer)
    database = Column(String)
    username = Column(String)
    password_encrypted = Column(String)
    is_active = Column(Boolean, default=True)
    ssl_config_id = Column(String, ForeignKey("ssl_certificates.id"), nullable=True)
    ssh_tunnel_id = Column(String, ForeignKey("ssh_tunnel_configs.id"), nullable=True)
    pool_settings = Column(JSON)
    advanced_settings = Column(JSON)
    last_heartbeat = Column(DateTime)
    status = Column(String, default="unknown")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    workspace = relationship("Workspace")
    ssl_config = relationship("SSLCertificate")
    ssh_tunnel = relationship("SSHTunnelConfig")

class SSHTunnelConfig(Base):
    __tablename__ = "ssh_tunnel_configs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String)
    ssh_host = Column(String)
    ssh_port = Column(Integer, default=22)
    ssh_user = Column(String)
    ssh_key_encrypted = Column(Text, nullable=True)
    ssh_passphrase_encrypted = Column(String, nullable=True)
    remote_bind_address = Column(String)
    local_bind_port = Column(Integer)

class SSLCertificate(Base):
    __tablename__ = "ssl_certificates"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String)
    ca_cert = Column(Text, nullable=True)
    client_cert = Column(Text, nullable=True)
    client_key_encrypted = Column(Text, nullable=True)
    verify_mode = Column(String, default="verify-full")
    expires_at = Column(DateTime, nullable=True)

class ConnectionHealthLog(Base):
    __tablename__ = "connection_health_logs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    connection_id = Column(String, ForeignKey("db_connections.id"), index=True)
    status = Column(String)
    latency_ms = Column(Float)
    error_message = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class ConnectionMetric(Base):
    __tablename__ = "connection_metrics"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    connection_id = Column(String, ForeignKey("db_connections.id"), index=True)
    metric_name = Column(String)
    value = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

# Phase 3: AI Memory & Analytics Metadata
class AIConversation(Base):
    __tablename__ = "ai_conversations"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    title = Column(String)
    history = Column(JSON)  # List of messages
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class AIContextMemory(Base):
    __tablename__ = "ai_context_memory"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    connection_id = Column(String, ForeignKey("db_connections.id"))
    entity_name = Column(String)  # Table or column name
    alias = Column(String)       # Business alias (e.g. "Monthly Revenue")
    description = Column(Text)
    metadata_ = Column("metadata", JSON)

class AISavedPrompt(Base):
    __tablename__ = "ai_saved_prompts"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    name = Column(String)
    prompt_text = Column(Text)
    category = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Dashboard(Base):
    __tablename__ = "dashboards"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    name = Column(String)
    config = Column(JSON)  # Layout and widget settings
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# SECTION 1 — SEMANTIC LAYER MODELS
class SemanticMetric(Base):
    __tablename__ = "semantic_metrics"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, index=True)
    description = Column(Text)
    formula = Column(Text)  # e.g. "SUM(revenue) - SUM(cost)"
    connection_id = Column(String, ForeignKey("db_connections.id"))
    metadata_ = Column("metadata", JSON)  # Formatting, unit, etc.

class SemanticDimension(Base):
    __tablename__ = "semantic_dimensions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, index=True)
    description = Column(Text)
    column_name = Column(String)
    table_name = Column(String)
    connection_id = Column(String, ForeignKey("db_connections.id"))

# SECTION 4 — NOTEBOOK MODELS
class NotebookSession(Base):
    __tablename__ = "notebook_sessions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    name = Column(String)
    cells = Column(JSON)  # List of cells: {type: 'sql'|'python'|'ai', content: '...'}
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

# SECTION 5 — ML & FORECASTING MODELS
class ForecastJob(Base):
    __tablename__ = "forecast_jobs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    metric_id = Column(String, ForeignKey("semantic_metrics.id"))
    parameters = Column(JSON)
    status = Column(String)  # pending, running, completed, failed
    results = Column(JSON)   # Serialized forecast points
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# SECTION 6 — DATA CATALOG MODELS
class CatalogIndex(Base):
    __tablename__ = "catalog_index"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    connection_id = Column(String, ForeignKey("db_connections.id"))
    entity_type = Column(String)  # table, column, metric
    entity_name = Column(String, index=True)
    entity_description = Column(Text)
    pii_tags = Column(JSON)  # List of identified PII (email, ssn, etc.)
    last_profiled = Column(DateTime)

# SECTION 10 — PLUGIN MODELS
class PluginRegistry(Base):
    __tablename__ = "plugin_registry"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True)
    version = Column(String)
    entry_point = Column(String)
    is_enabled = Column(Boolean, default=True)
# SECTION 2 — WORKSPACE MODELS
class Workspace(Base):
    __tablename__ = "workspaces"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True)
    slug = Column(String, unique=True)
    settings = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class WorkspaceMember(Base):
    __tablename__ = "workspace_members"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String, ForeignKey("workspaces.id"))
    user_id = Column(String, ForeignKey("users.id"))
    role = Column(String)  # owner, admin, editor, viewer

# SECTION 5 — ADVANCED SEMANTIC MODELS
class SemanticCertification(Base):
    __tablename__ = "semantic_certifications"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    metric_id = Column(String, ForeignKey("semantic_metrics.id"))
    certified_by = Column(String, ForeignKey("users.id"))
    certification_status = Column(String)  # certified, draft, deprecated
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class SemanticDependency(Base):
    __tablename__ = "semantic_dependencies"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    parent_id = Column(String)  # metric or dimension id
    child_id = Column(String)
    dependency_type = Column(String)

# SECTION 8 — RESOURCE GOVERNANCE MODELS
class ResourceUsageLog(Base):
    __tablename__ = "resource_usage_logs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    workspace_id = Column(String, ForeignKey("workspaces.id"))
    resource_type = Column(String)  # memory, cpu, tokens
    amount = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

# SECTION 10 — COLLABORATION MODELS
class CollaborationSession(Base):
    __tablename__ = "collaboration_sessions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String, ForeignKey("workspaces.id"))
    entity_type = Column(String)  # dashboard, notebook
    entity_id = Column(String)
    shared_with = Column(JSON)  # List of user_ids
# SECTION 4 — PLUGIN MODELS
class Plugin(Base):
    __tablename__ = "plugins"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True)
    version = Column(String)
    developer = Column(String)
    is_signed = Column(Boolean, default=False)
    permissions = Column(JSON)
    config = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# SECTION 7 — AI KNOWLEDGE MODELS
class AIKnowledgeNode(Base):
    __tablename__ = "ai_knowledge_graph"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_type = Column(String)  # concept, relationship, rule
    content = Column(JSON)
    embedding = Column(JSON)  # Vector embedding for search
    last_validated = Column(DateTime)

class AIReasoningLog(Base):
    __tablename__ = "ai_reasoning_logs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    request_id = Column(String)
    thought_chain = Column(JSON)
    confidence_score = Column(Float)
    grounding_references = Column(JSON)

# SECTION 11 — LICENSING MODELS
class License(Base):
    __tablename__ = "licenses"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    key_hash = Column(String, unique=True)
    plan_type = Column(String)  # community, pro, enterprise
    seats = Column(Integer)
    expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)

# SECTION 2 — UPDATE MODELS
class UpdateHistory(Base):
    __tablename__ = "update_history"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    version = Column(String)
    applied_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String)  # success, rolled_back
