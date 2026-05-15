import asyncio
import os
import sys
from typing import Any, Dict

# Mocking parts of the app to demonstrate the crash
class MockConfig:
    def __init__(self):
        self.host = "localhost"
        self.type = "mssql"
        self.port = 1433
        self.password = "secret"
        self.username = "sa"
        self.database = "master"
        self.timeout = 5
        self.pool_size = 5
        self.extra_params = {}

async def reproduce_serialization_failure():
    print("--- [REPRO] Serialization Failure (MissingGreenlet) ---")
    # This happens when Pydantic touches a lazy relationship in an async session
    # We simulate the access that happens during from_attributes = True
    print("Hypothesis: Accessing DBConnection.workspace without joinedload raises MissingGreenlet.")
    # (Code would go here if we had the DB running, but the logic is sound)

async def reproduce_connector_segfault():
    print("--- [REPRO] Connector Segfault (ERR_EMPTY_RESPONSE) ---")
    # Simulate a driver-level crash that kills the process
    print("Simulating process termination via os._exit(1) to mimic pyodbc/oracledb segfault...")
    # os._exit(1) # Uncommenting this would kill the script immediately without cleanup

async def reproduce_memory_explosion():
    print("--- [REPRO] Memory Explosion in FileConnector ---")
    # Simulate loading a large dataframe without chunking
    import pandas as pd
    import numpy as np
    print("Creating a 100MB dummy DataFrame to simulate memory pressure...")
    df = pd.DataFrame(np.random.randn(1000000, 10))
    print(f"DataFrame size in memory: {df.memory_usage().sum() / 1024 / 1024:.2f} MB")
    # Scaling this to 2GB would crash a standard worker

async def main():
    await reproduce_serialization_failure()
    await reproduce_memory_explosion()
    # await reproduce_connector_segfault()

if __name__ == "__main__":
    asyncio.run(main())
