import asyncio

import pytest

from app.api.chat import _stream_sse_events


class FakeRequest:
    def __init__(self, disconnect_after=None):
        self.calls = 0
        self.disconnect_after = disconnect_after

    async def is_disconnected(self):
        self.calls += 1
        return self.disconnect_after is not None and self.calls >= self.disconnect_after


async def collect(generator):
    return [event async for event in generator]


@pytest.mark.asyncio
async def test_stream_preserves_data_and_done_format():
    async def chunks():
        yield "first"
        yield "second"

    events = await collect(_stream_sse_events(chunks(), FakeRequest(), 0.05))

    assert events[0] == 'data: {"delta": "first"}\n\n'
    assert events[1] == 'data: {"delta": "second"}\n\n'
    assert events[-1] == "data: [DONE]\n\n"


@pytest.mark.asyncio
async def test_heartbeat_is_emitted_while_model_is_idle():
    async def chunks():
        await asyncio.sleep(0.06)
        yield "ready"

    events = await collect(_stream_sse_events(chunks(), FakeRequest(), 0.01))

    assert events.count(": heartbeat\n\n") >= 3
    assert events[-1] == "data: [DONE]\n\n"


@pytest.mark.asyncio
async def test_disconnect_closes_pending_model_generator_without_done():
    closed = asyncio.Event()

    async def chunks():
        try:
            await asyncio.sleep(10)
            yield "never"
        finally:
            closed.set()

    events = await collect(_stream_sse_events(chunks(), FakeRequest(disconnect_after=2), 0.01))

    assert events == []
    assert closed.is_set()


@pytest.mark.asyncio
async def test_model_exception_is_not_reflected_to_client():
    async def chunks():
        raise RuntimeError("private-key-material")
        yield  # pragma: no cover

    events = await collect(_stream_sse_events(chunks(), FakeRequest(), 0.01))

    assert events == ['event: error\ndata: {"error":"AI_STREAM_FAILED"}\n\n']
    assert "private-key-material" not in events[0]
