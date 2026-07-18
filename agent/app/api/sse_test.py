"""Protected deterministic SSE provider, registered only when SSE_TEST_MODE is enabled."""
import asyncio
import json
import time
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

router = APIRouter()
request_states: dict[str, str] = {}


@router.post("/test/sse")
async def deterministic_sse(request: Request, spec: dict[str, Any]):
    mode = str(spec.get("mode", "events"))
    request_id = str(spec.get("request_id", "anonymous"))[:80]
    interval = max(float(spec.get("interval", 1.0)), 0.01)
    duration = max(float(spec.get("duration", 3.0)), 0.01)
    if mode == "error4xx":
        raise HTTPException(status_code=422, detail="test rejection")
    if mode == "error5xx":
        raise HTTPException(status_code=500, detail="test upstream failure")

    async def events():
        started = time.monotonic()
        sequence = 0
        request_states[request_id] = "running"
        try:
            if mode == "idle":
                await asyncio.sleep(duration)
                yield "data: [DONE]\n\n"
                return
            while time.monotonic() - started < duration:
                if await request.is_disconnected():
                    return
                await asyncio.sleep(interval)
                if mode == "heartbeat":
                    yield ": heartbeat\n\n"
                else:
                    yield "data: " + json.dumps({"delta": str(sequence)}) + "\n\n"
                    sequence += 1
            yield "data: [DONE]\n\n"
        except asyncio.CancelledError:
            request_states[request_id] = "cancelled"
            raise
        finally:
            if await request.is_disconnected():
                request_states[request_id] = "cancelled"
            elif request_states.get(request_id) == "running":
                request_states[request_id] = "completed"

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no"},
    )


@router.get("/test/sse/cancellations/{request_id}")
async def cancellation_status(request_id: str):
    state = request_states.get(request_id, "unknown")
    return {"request_id": request_id, "state": state, "cancelled": state == "cancelled"}
