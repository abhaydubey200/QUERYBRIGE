import asyncio
import httpx
import time
import uuid

API_URL = "http://localhost:8000/api/v1"

async def test_connection_endpoint(client: httpx.AsyncClient, name: str):
    payload = {
        "db_type": "postgres",
        "name": f"Stress Test {name}",
        "host": "invalid_host_repro",
        "port": 5432,
        "username": "admin",
        "password": "password",
        "database": "querybridge"
    }
    start = time.perf_counter()
    try:
        response = await client.post(f"{API_URL}/connections/test", json=payload, timeout=10.0)
        duration = time.perf_counter() - start
        if response.status_code == 200:
            result = response.json()
            status = "PASSED" if result.get("success") else "FAILED (Logic)"
            err = result.get("error") or {}
            print(f"[{name}] {status} | Msg: {err.get('message', 'N/A')} | Trace: {err.get('trace_id', 'N/A')}")
        else:
            try:
                result = response.json()
                err = result.get("error") or {}
                print(f"[{name}] HTTP {response.status_code} | Msg: {err.get('message', 'N/A')} | Trace: {err.get('trace_id', 'N/A')}")
            except:
                print(f"[{name}] HTTP {response.status_code} | RAW: {response.text[:100]}")
    except Exception as e:
        print(f"[{name}] REQUEST FAILED: {str(e)}")

async def run_stress_test(concurrent_requests: int):
    print(f"--- Starting Stress Test with {concurrent_requests} concurrent requests ---")
    async with httpx.AsyncClient() as client:
        tasks = [test_connection_endpoint(client, f"Req-{i}") for i in range(concurrent_requests)]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    # Simulate 20 concurrent failing connection tests
    asyncio.run(run_stress_test(20))
