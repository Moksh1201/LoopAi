import os
import uuid
import asyncio
import heapq
from enum import Enum
from typing import List, Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field, validator

RATE_LIMIT_SECONDS = float(os.getenv("RATE_LIMIT_SECONDS", "5"))
MAX_ID = 10**9 + 7

class Priority(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class IngestRequest(BaseModel):
    ids: List[int] = Field(..., example=[1, 2, 3, 4, 5], min_items=1)
    priority: Priority = Field(..., example="MEDIUM")

    @validator('ids')
    def validate_ids(cls, v):
        for id in v:
            if not (1 <= id <= MAX_ID):
                raise ValueError(f"ID must be between 1 and {MAX_ID}")
        return v

class BatchInfo(BaseModel):
    batch_id: str
    ids: List[int]
    status: str 

class StatusResponse(BaseModel):
    ingestion_id: str
    status: str 
    batches: List[BatchInfo]


INGESTIONS: Dict[str, Dict[str, Any]] = {}


PENDING_BATCHES: List[Any] = []
PENDING_LOCK = asyncio.Lock()


def _priority_rank(p: Priority) -> int:
    return {"HIGH": 1, "MEDIUM": 2, "LOW": 3}[p.value]


app = FastAPI(title="Data Ingestion API System", version="1.0.0")


@app.on_event("startup")
async def startup_event():
  
    asyncio.create_task(_batch_worker())


@app.post("/ingest", status_code=201)
async def ingest(request: IngestRequest):

    ingestion_id = str(uuid.uuid4())
    now = datetime.utcnow()

    batches = []
    for i in range(0, len(request.ids), 3):
        batch_ids = request.ids[i : i + 3]
        batch_id = str(uuid.uuid4())
        batches.append((batch_id, batch_ids))

    INGESTIONS[ingestion_id] = {
        "priority": request.priority,
        "created_at": now,
        "batches": {},
    }

    for batch_id, batch_ids in batches:
        INGESTIONS[ingestion_id]["batches"][batch_id] = {
            "ids": batch_ids.copy(),
            "status": "yet_to_start",
            "created_at": now
        }

        pr = _priority_rank(request.priority)
        entry = (pr, now, ingestion_id, batch_id, batch_ids.copy())
        async with PENDING_LOCK:
            heapq.heappush(PENDING_BATCHES, entry)

    return {"ingestion_id": ingestion_id}


@app.get("/status/{ingestion_id}", response_model=StatusResponse)
async def status(ingestion_id: str):
   
    data = INGESTIONS.get(ingestion_id)
    if data is None:
        raise HTTPException(status_code=404, detail="ingestion_id not found")

    batches = []
    statuses = []
    for batch_id, info in data["batches"].items():
        batches.append(BatchInfo(
            batch_id=batch_id,
            ids=info["ids"],
            status=info["status"]
        ))
        statuses.append(info["status"])

    if all(s == "yet_to_start" for s in statuses):
        overall = "yet_to_start"
    elif all(s == "completed" for s in statuses):
        overall = "completed"
    else:
        overall = "triggered"

    return StatusResponse(
        ingestion_id=ingestion_id,
        status=overall,
        batches=batches
    )


async def _batch_worker():
  
    while True:
        await asyncio.sleep(0)  
        async with PENDING_LOCK:
            if not PENDING_BATCHES:
                pass
            else:
                pr, created_at, ingestion_id, batch_id, ids_list = heapq.heappop(PENDING_BATCHES)

                INGESTIONS[ingestion_id]["batches"][batch_id]["status"] = "triggered"

                await _process_batch(ingestion_id, batch_id, ids_list)

                INGESTIONS[ingestion_id]["batches"][batch_id]["status"] = "completed"

                await asyncio.sleep(RATE_LIMIT_SECONDS)

        if not PENDING_BATCHES:
            await asyncio.sleep(0.5)


async def _process_batch(ingestion_id: str, batch_id: str, ids_list: List[int]):
    """Simulate processing each ID by calling an external API."""
    for _id in ids_list:
        await asyncio.sleep(0.5 + asyncio.get_event_loop().time() % 1.0)
        response = {"id": _id, "data": f"processed_{_id}"}
    return


