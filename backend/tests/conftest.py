"""
QueryBridge Test Infrastructure

Provides shared fixtures, mocks, and utilities for all test suites.
"""

import pytest
import asyncio
from typing import Generator, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timedelta

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool

from app.models import Base
from app.db.session import get_db as get_db_session


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Create in-memory SQLite database for testing.
    
    Yields:
        AsyncSession connected to test database
    """
    # Create in-memory engine
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        echo=False,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async_session = AsyncSession(bind=engine, expire_on_commit=False)

    yield async_session

    # Cleanup
    await async_session.close()
    await engine.dispose()


@pytest.fixture
async def db_session(test_db: AsyncSession) -> AsyncSession:
    """
    Provides a fresh database session for each test.
    """
    async with test_db:
        yield test_db


# ============================================================================
# MOCK DATABASE FIXTURES
# ============================================================================

@pytest.fixture
def mock_table_data() -> dict:
    """Mock table metadata for testing"""
    return {
        "table_id": str(uuid4()),
        "name": "customers",
        "schema": "public",
        "row_count": 50000,
        "column_count": 15,
        "last_updated": datetime.now(),
        "description": "Customer master data",
    }


@pytest.fixture
def mock_column_data() -> dict:
    """Mock column metadata for testing"""
    return {
        "column_id": str(uuid4()),
        "table_id": str(uuid4()),
        "name": "email",
        "data_type": "VARCHAR(255)",
        "nullable": True,
        "is_primary_key": False,
        "is_foreign_key": False,
        "null_percentage": 2.5,
        "distinct_percentage": 98.5,
    }


@pytest.fixture
def mock_pii_column_data() -> dict:
    """Mock PII column metadata for testing"""
    return {
        "column_id": str(uuid4()),
        "table_id": str(uuid4()),
        "name": "ssn",
        "data_type": "VARCHAR(11)",
        "nullable": False,
        "is_pii": True,
        "pii_type": "ssn",
        "confidence": 0.95,
        "detection_method": "regex",
    }


@pytest.fixture
def mock_relationship_data() -> dict:
    """Mock relationship data for testing"""
    return {
        "source_table_id": str(uuid4()),
        "target_table_id": str(uuid4()),
        "join_keys": ["customer_id"],
        "cardinality": "1:N",
        "confidence": 0.95,
        "is_foreign_key": True,
    }


@pytest.fixture
def mock_lineage_edge() -> dict:
    """Mock lineage edge for testing"""
    return {
        "source_id": str(uuid4()),
        "target_id": str(uuid4()),
        "edge_type": "table_lineage",
        "confidence": 0.85,
        "description": "CTAS from source_table",
    }


@pytest.fixture
def mock_anomaly_data() -> dict:
    """Mock anomaly detection data for testing"""
    return {
        "anomaly_type": "row_spike",
        "severity": "high",
        "baseline_value": 10000,
        "current_value": 35000,
        "deviation_pct": 250,
        "description": "Row count increased 250% in last 24 hours",
        "suggested_action": "Investigate ETL processes",
    }


# ============================================================================
# API MOCK FIXTURES
# ============================================================================

@pytest.fixture
def mock_api_response_success() -> dict:
    """Successful API response template"""
    return {
        "success": True,
        "data": {
            "id": str(uuid4()),
            "name": "test_resource",
        },
        "timestamp": datetime.now().isoformat(),
    }


@pytest.fixture
def mock_api_response_error() -> dict:
    """Error API response template"""
    return {
        "success": False,
        "error": "Resource not found",
        "status_code": 404,
        "timestamp": datetime.now().isoformat(),
    }


# ============================================================================
# MOCK SERVICE FIXTURES
# ============================================================================

@pytest.fixture
def mock_schema_discovery_service():
    """Mock SchemaDiscovery service"""
    mock_service = AsyncMock()
    mock_service.discover_schemas = AsyncMock(return_value=["public", "analytics"])
    mock_service.discover_tables = AsyncMock(return_value=[])
    mock_service.discover_columns = AsyncMock(return_value=[])
    return mock_service


@pytest.fixture
def mock_profiler_service():
    """Mock TableProfiler service"""
    mock_service = AsyncMock()
    mock_service.profile_table = AsyncMock(return_value={
        "row_count": 50000,
        "null_percentages": {},
        "distinct_percentages": {},
    })
    mock_service.profile_column = AsyncMock(return_value={
        "data_type": "VARCHAR",
        "null_percentage": 2.5,
        "distinct_percentage": 98.5,
        "min_length": 5,
        "max_length": 255,
    })
    return mock_service


@pytest.fixture
def mock_pii_detector_service():
    """Mock PII Detector service"""
    mock_service = AsyncMock()
    mock_service.detect_pii_columns = AsyncMock(return_value=[{
        "column_id": str(uuid4()),
        "pii_type": "email",
        "confidence": 0.95,
        "detection_method": "regex",
    }])
    return mock_service


@pytest.fixture
def mock_quality_scorer_service():
    """Mock DataQualityScorer service"""
    mock_service = AsyncMock()
    mock_service.score_table_quality = AsyncMock(return_value={
        "freshness_score": 0.95,
        "completeness_score": 0.98,
        "uniqueness_score": 0.99,
        "overall_score": 0.97,
    })
    return mock_service


@pytest.fixture
def mock_relationship_engine_service():
    """Mock RelationshipEngine service"""
    mock_service = AsyncMock()
    mock_service.discover_relationships = AsyncMock(return_value=[{
        "source_table_id": str(uuid4()),
        "target_table_id": str(uuid4()),
        "join_keys": ["id"],
        "cardinality": "1:N",
        "confidence": 0.95,
    }])
    return mock_service


@pytest.fixture
def mock_lineage_service():
    """Mock LineageTracker service"""
    mock_service = AsyncMock()
    mock_service.extract_lineage = AsyncMock(return_value=[{
        "source_table": "staging.orders",
        "target_table": "analytics.orders_fact",
        "confidence": 0.85,
        "lineage_type": "CTAS",
    }])
    return mock_service


@pytest.fixture
def mock_anomaly_detector_service():
    """Mock AnomalyDetector service"""
    mock_service = AsyncMock()
    mock_service.detect_anomalies = AsyncMock(return_value=[{
        "anomaly_type": "row_spike",
        "severity": "high",
        "baseline_value": 10000,
        "current_value": 35000,
        "deviation_pct": 250,
    }])
    return mock_service


@pytest.fixture
def mock_semantic_search_service():
    """Mock SemanticSearch service"""
    mock_service = AsyncMock()
    mock_service.search = AsyncMock(return_value=[{
        "id": str(uuid4()),
        "resource_type": "table",
        "name": "customers",
        "combined_score": 0.95,
        "matches": ["customer", "custm"],
    }])
    return mock_service


# ============================================================================
# MOCK DATABASE CONNECTION FIXTURES
# ============================================================================

@pytest.fixture
def mock_postgres_connection():
    """Mock PostgreSQL connection"""
    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock(return_value=MagicMock(
        fetchall=lambda: [("public",), ("information_schema",)]
    ))
    return mock_conn


@pytest.fixture
def mock_mysql_connection():
    """Mock MySQL connection"""
    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock(return_value=MagicMock(
        fetchall=lambda: [("mysql",), ("performance_schema",)]
    ))
    return mock_conn


@pytest.fixture
def mock_mssql_connection():
    """Mock MSSQL connection"""
    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock(return_value=MagicMock(
        fetchall=lambda: [("dbo",), ("sys",)]
    ))
    return mock_conn


# ============================================================================
# TEST DATA GENERATORS
# ============================================================================

class TestDataGenerator:
    """Helper class to generate test data"""

    @staticmethod
    def create_table(
        name: str = "test_table",
        row_count: int = 10000,
    ) -> dict:
        """Create mock table data"""
        return {
            "table_id": str(uuid4()),
            "name": name,
            "schema": "public",
            "row_count": row_count,
            "column_count": 5,
            "last_updated": datetime.now(),
        }

    @staticmethod
    def create_column(
        name: str = "test_column",
        data_type: str = "VARCHAR",
        is_pii: bool = False,
    ) -> dict:
        """Create mock column data"""
        return {
            "column_id": str(uuid4()),
            "table_id": str(uuid4()),
            "name": name,
            "data_type": data_type,
            "nullable": True,
            "is_pii": is_pii,
            "null_percentage": 5.0 if not is_pii else 1.0,
            "distinct_percentage": 95.0,
        }

    @staticmethod
    def create_pii_columns() -> list:
        """Create mock PII columns (one of each type)"""
        pii_types = [
            ("email", "email@domain.com"),
            ("ssn", "123-45-6789"),
            ("credit_card", "4532-1111-2222-3333"),
            ("phone", "555-123-4567"),
            ("address", "123 Main St, City, State 12345"),
        ]
        
        columns = []
        for pii_type, example in pii_types:
            columns.append({
                "column_id": str(uuid4()),
                "name": pii_type,
                "data_type": "VARCHAR",
                "is_pii": True,
                "pii_type": pii_type,
                "confidence": 0.95,
                "example_value": example,
            })
        return columns

    @staticmethod
    def create_lineage_graph(node_count: int = 100) -> list:
        """Create mock lineage edges for a graph"""
        edges = []
        node_ids = [str(uuid4()) for _ in range(node_count)]
        
        for i in range(len(node_ids) - 1):
            edges.append({
                "source_id": node_ids[i],
                "target_id": node_ids[i + 1],
                "confidence": 0.85 + (i % 10) * 0.01,
                "lineage_type": "CTAS" if i % 3 == 0 else "INSERT_SELECT",
            })
        return edges

    @staticmethod
    def create_anomalies(count: int = 5) -> list:
        """Create mock anomaly detections"""
        anomaly_types = ["row_spike", "null_increase", "cardinality_shift", "freshness_delay"]
        severities = ["low", "medium", "high", "critical"]
        
        anomalies = []
        for i in range(count):
            anomalies.append({
                "anomaly_type": anomaly_types[i % len(anomaly_types)],
                "severity": severities[i % len(severities)],
                "baseline_value": 10000 + i * 1000,
                "current_value": 15000 + i * 1000,
                "deviation_pct": 50 + i * 10,
                "description": f"Test anomaly {i}",
            })
        return anomalies


@pytest.fixture
def test_data_generator() -> TestDataGenerator:
    """Provides TestDataGenerator for creating mock data"""
    return TestDataGenerator()


# ============================================================================
# PARAMETERIZATION FIXTURES
# ============================================================================

@pytest.fixture(params=["postgres", "mysql", "mssql", "oracle", "snowflake"])
def all_database_types(request):
    """Parametrized fixture for all supported database types"""
    return request.param


@pytest.fixture(params=["low", "medium", "high", "critical"])
def all_severity_levels(request):
    """Parametrized fixture for all severity levels"""
    return request.param


@pytest.fixture(params=["email", "ssn", "credit_card", "phone", "name", "generic"])
def all_pii_types(request):
    """Parametrized fixture for all PII types"""
    return request.param


# ============================================================================
# PERFORMANCE TESTING FIXTURES
# ============================================================================

@pytest.fixture
def benchmark_timer():
    """Timer for performance benchmarking"""
    class BenchmarkTimer:
        def __init__(self):
            self.start_time = None
            self.elapsed = None

        def start(self):
            self.start_time = datetime.now()

        def stop(self):
            self.elapsed = (datetime.now() - self.start_time).total_seconds()
            return self.elapsed

        def assert_under(self, max_seconds: float):
            assert self.elapsed < max_seconds, f"Execution took {self.elapsed}s, max {max_seconds}s"

    return BenchmarkTimer()


# ============================================================================
# MARKERS
# ============================================================================

def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "security: mark test as a security test")
    config.addinivalue_line("markers", "load: mark test as a load test")
    config.addinivalue_line("markers", "slow: mark test as slow (skip in quick runs)")
    config.addinivalue_line("markers", "postgres: mark test as PostgreSQL specific")
    config.addinivalue_line("markers", "mysql: mark test as MySQL specific")
    config.addinivalue_line("markers", "mssql: mark test as MSSQL specific")
    config.addinivalue_line("markers", "oracle: mark test as Oracle specific")
    config.addinivalue_line("markers", "snowflake: mark test as Snowflake specific")
