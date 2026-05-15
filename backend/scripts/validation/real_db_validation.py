
import asyncio
import time
import logging
import os
from typing import Dict, Any, List
from app.connectors.connector_factory import ConnectorFactory
from app.connectors.base_connector import ConnectionConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("operational_validation")

async def validate_connector(name: str, config: Dict[str, Any]):
    logger.info(f"🚀 Validating {name} connector...")
    start_time = time.perf_counter()
    
    try:
        conn_config = ConnectionConfig(**config)
        connector = ConnectorFactory.get_connector(conn_config)
        
        # 1. Test Connection
        result = await connector.test_connection()
        if not result.success:
            logger.error(f"❌ {name} Connection Failed: {result.message}")
            return False
            
        logger.info(f"✅ {name} Connection Successful ({result.latency_ms}ms) - Version: {result.server_version}")
        
        # 2. Metadata Discovery
        schemas = await connector.get_schemas()
        logger.info(f"✅ {name} Schemas discovered: {len(schemas)}")
        
        if schemas:
            tables = await connector.get_tables(schemas[0])
            logger.info(f"✅ {name} Tables in {schemas[0]}: {len(tables)}")
            
            if tables:
                columns = await connector.get_columns(tables[0].name, schemas[0])
                logger.info(f"✅ {name} Columns in {tables[0].name}: {len(columns)}")
        
        # 3. Streaming Test
        logger.info(f"⏳ {name} Running streaming test...")
        query = "SELECT 1 as val" # Simple test query
        if name == "Oracle":
            query = "SELECT 1 as val FROM DUAL"
            
        row_count = 0
        async for row in connector.stream_query(query):
            row_count += 1
            if row_count >= 1: break
            
        logger.info(f"✅ {name} Streaming test passed.")
        
        latency = (time.perf_counter() - start_time) * 1000
        logger.info(f"🏆 {name} Operational Validation Completed in {latency:.2f}ms")
        return True
        
    except Exception as e:
        logger.error(f"💥 {name} Validation Crashed: {str(e)}")
        return False

async def main():
    # Credentials from docker-compose.yml
    db_configs = {
        "PostgreSQL": {
            "type": "postgres",
            "host": "localhost",
            "port": 5432,
            "username": "admin",
            "password": "password123",
            "database": "querybridge"
        },
        "MySQL": {
            "type": "mysql",
            "host": "localhost",
            "port": 3306,
            "username": "admin",
            "password": "password123",
            "database": "querybridge_test"
        },
        "MSSQL": {
            "type": "mssql",
            "host": "localhost",
            "port": 1433,
            "username": "sa",
            "password": "Password123!",
            "database": "master"
        },
        "Oracle": {
            "type": "oracle",
            "host": "localhost",
            "port": 1521,
            "username": "admin",
            "password": "password123",
            "database": "FREEPDB1" # Default for Oracle Free
        }
    }
    if os.getenv("SNOWFLAKE_ACCOUNT") and os.getenv("SNOWFLAKE_USER"):
        db_configs["Snowflake"] = {
            "type": "snowflake",
            "host": os.getenv("SNOWFLAKE_ACCOUNT"),
            "port": 443,
            "username": os.getenv("SNOWFLAKE_USER"),
            "password": os.getenv("SNOWFLAKE_PASSWORD", ""),
            "database": os.getenv("SNOWFLAKE_DATABASE"),
            "schema_name": os.getenv("SNOWFLAKE_SCHEMA"),
            "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
            "role": os.getenv("SNOWFLAKE_ROLE"),
            "extra_params": {
                "authenticator": os.getenv("SNOWFLAKE_AUTHENTICATOR"),
            },
        }
    else:
        logger.warning("Snowflake validation skipped: SNOWFLAKE_ACCOUNT/SNOWFLAKE_USER not configured")
    
    results = {}
    for name, config in db_configs.items():
        results[name] = await validate_connector(name, config)
        
    logger.info("\n" + "="*50)
    logger.info("FINAL OPERATIONAL DATABASE CERTIFICATION SUMMARY")
    logger.info("="*50)
    for name, success in results.items():
        status = "PASSED" if success else "FAILED"
        logger.info(f"{name:15} : {status}")
    logger.info("="*50)

if __name__ == "__main__":
    asyncio.run(main())
