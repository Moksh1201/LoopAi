import os
import pytest
import asyncio
import time
from httpx import AsyncClient

import app as ingestion_app

os.environ["RATE_LIMIT_SECONDS"] = "1.0"

ingestion_app.RATE_LIMIT_SECONDS = float(os.getenv("RATE_LIMIT_SECONDS"))

@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="module")
async def client():
    """
    Launch the FastAPI app with an AsyncClient.
    """
    async with AsyncClient(app=ingestion_app.app, base_url="http://test") as ac:
        yield ac

@pytest.mark.anyio
async def test_single_ingestion_and_status_transitions(client):
    payload = {"ids": [1, 2, 3, 4, 5], "priority": "MEDIUM"}
    resp = await client.post("/ingest", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    ingestion_id = data["ingestion_id"]
    assert isinstance(ingestion_id, str)

    status_resp = await client.get(f"/status/{ingestion_id}")
    assert status_resp.status_code == 200
    st = status_resp.json()
    assert len(st["batches"]) == 2
    for b in st["batches"]:
        assert b["status"] == "yet_to_start"
    assert st["status"] == "yet_to_start"

    await asyncio.sleep(1.2)
    status_resp = await client.get(f"/status/{ingestion_id}")
    st = status_resp.json()
    statuses = {b["status"] for b in st["batches"]}
    assert "completed" in statuses
    assert "yet_to_start" in statuses
    assert st["status"] == "triggered"

    await asyncio.sleep(1.2)
    status_resp = await client.get(f"/status/{ingestion_id}")
    st = status_resp.json()
    assert all(b["status"] == "completed" for b in st["batches"])
    assert st["status"] == "completed"


@pytest.mark.anyio
async def test_priority_preemption(client):
    """
    Submit a LOW‐priority ingestion, then shortly after a HIGH‐priority one,
    and verify that HIGH runs first (respecting FIFO within same priority).
    """
    low_payload = {"ids": [10, 20, 30], "priority": "LOW"}
    low_resp = await client.post("/ingest", json=low_payload)
    assert low_resp.status_code == 201
    low_id = low_resp.json()["ingestion_id"]

    await asyncio.sleep(0.2)
    high_payload = {"ids": [100, 200, 300], "priority": "HIGH"}
    high_resp = await client.post("/ingest", json=high_payload)
    assert high_resp.status_code == 201
    high_id = high_resp.json()["ingestion_id"]

    st_low = (await client.get(f"/status/{low_id}")).json()
    st_high = (await client.get(f"/status/{high_id}")).json()
    assert all(b["status"] == "yet_to_start" for b in st_low["batches"])
    assert all(b["status"] == "yet_to_start" for b in st_high["batches"])
    assert st_low["status"] == "yet_to_start"
    assert st_high["status"] == "yet_to_start"

    await asyncio.sleep(1.2)
    st_low = (await client.get(f"/status/{low_id}")).json()
    st_high = (await client.get(f"/status/{high_id}")).json()

    assert all(b["status"] == "completed" for b in st_high["batches"])
    assert st_high["status"] == "completed"

    assert all(b["status"] == "yet_to_start" for b in st_low["batches"])
    assert st_low["status"] == "yet_to_start"

    await asyncio.sleep(1.2)
    st_low = (await client.get(f"/status/{low_id}")).json()
    assert all(b["status"] == "completed" for b in st_low["batches"])
    assert st_low["status"] == "completed"


@pytest.mark.anyio
async def test_invalid_inputs(client):
    resp = await client.post("/ingest", json={"priority": "HIGH"})
    assert resp.status_code == 422

    resp = await client.post("/ingest", json={"ids": [], "priority": "LOW"})
    assert resp.status_code == 422

    resp = await client.post("/ingest", json={"ids": [1, 2], "priority": "NOT_A_PRI"})
    assert resp.status_code == 422

    resp = await client.get("/status/nonexistent-id")
    assert resp.status_code == 404
