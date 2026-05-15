import os
import pytest
import pandas as pd
import asyncio
from app.connectors.file_connector import FileConnector
from app.connectors.base_connector import ConnectionConfig

@pytest.fixture
def sample_csv(tmp_path):
    f = tmp_path / "test_data.csv"
    df = pd.DataFrame({
        "id": [1, 2, 3],
        "city": ["New York", "London", "Tokyo"],
        "population": [8000000, 9000000, 14000000]
    })
    df.to_csv(f, index=False)
    return str(f)

@pytest.fixture
def sample_excel(tmp_path):
    f = tmp_path / "test_data.xlsx"
    df = pd.DataFrame({
        "id": [1, 2],
        "product": ["Widget", "Gadget"],
        "price": [19.99, 29.99]
    })
    df.to_excel(f, index=False)
    return str(f)

@pytest.mark.asyncio
async def test_file_connector_csv_streaming(sample_csv):
    config = ConnectionConfig(
        name="CSV Test",
        type="csv",
        host=sample_csv,
        username="system"
    )
    connector = FileConnector(config)
    
    # Test connectivity
    result = await connector.test_connection()
    assert result.success is True
    assert result.diagnostics["file_path"] == sample_csv
    
    # Test table discovery
    tables = await connector.get_tables()
    assert len(tables) == 1
    assert tables[0].name == "test_data"
    
    # Test streaming query
    rows = []
    async for row in connector.stream_query("SELECT * FROM test_data WHERE population > 8500000"):
        rows.append(row)
    
    assert len(rows) == 2
    assert rows[0]["city"] == "London"
    assert rows[1]["city"] == "Tokyo"
    
    await connector.disconnect()

@pytest.mark.asyncio
async def test_file_connector_excel(sample_excel):
    config = ConnectionConfig(
        name="Excel Test",
        type="excel",
        host=sample_excel,
        username="system"
    )
    connector = FileConnector(config)
    
    # Test table discovery
    tables = await connector.get_tables()
    assert tables[0].name == "test_data"
    
    # Test query
    rows = []
    async for row in connector.stream_query("SELECT product FROM test_data ORDER BY price DESC LIMIT 1"):
        rows.append(row)
    
    assert len(rows) == 1
    assert rows[0]["product"] == "Gadget"
    
    await connector.disconnect()

@pytest.mark.asyncio
async def test_file_connector_invalid_path():
    config = ConnectionConfig(
        name="Invalid Test",
        type="csv",
        host="/non/existent/path.csv",
        username="system"
    )
    connector = FileConnector(config)
    result = await connector.test_connection()
    assert result.success is False
    assert "File not found" in result.message
