"""AgentOS Core test fixtures for application-neutral tool runtime injection."""

import asyncio
import inspect
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


AGENTOS_ROOT = Path(__file__).resolve().parents[1]
AGENTOS_SRC = AGENTOS_ROOT / "src"

value = str(AGENTOS_SRC)
if value not in sys.path:
    sys.path.insert(0, value)


from agentos.adapters.tool_adapter import (
    clear_tool_runtime_factory,
    register_tool_runtime_factory,
)


class _Source:
    citation_id = "src_agentos_test"

    def public_dict(self):
        return {
            "citationId": self.citation_id,
            "title": "AgentOS test evidence",
            "url": "https://example.test/agentos-evidence",
            "provider": "test-fixture",
            "retrievedAt": "2026-01-01T00:00:00+00:00",
        }


class _Execution:
    tool_name = "knowledge_search"

    def public_dict(self):
        return {
            "callId": "call_agentos_test",
            "toolName": self.tool_name,
            "status": "completed",
            "durationMs": 1,
            "inputSummary": "query",
            "outputSummary": "Found test evidence.",
            "sourceRefs": [_Source.citation_id],
        }


class _ToolRuntime:
    def scoped(self, allowed_tools):
        return self

    async def run(self, text, **kwargs):
        return SimpleNamespace(
            text="Evidence-backed result from the AgentOS test fixture.",
            sources=[_Source()],
            tool_executions=[_Execution()],
        )


@pytest.fixture(autouse=True)
def _configured_tool_runtime():
    register_tool_runtime_factory(_ToolRuntime)
    yield
    clear_tool_runtime_factory()


def pytest_pyfunc_call(pyfuncitem):
    """Run async test functions without requiring an extra pytest plugin."""

    test_func = pyfuncitem.obj
    if not inspect.iscoroutinefunction(test_func):
        return None

    kwargs = {
        name: pyfuncitem.funcargs[name]
        for name in pyfuncitem._fixtureinfo.argnames
    }
    asyncio.run(test_func(**kwargs))
    return True
