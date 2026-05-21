import asyncio
import inspect
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
AGENTOS_SRC = PROJECT_ROOT / "agentOS" / "src"
AGENT_APP_ROOT = PROJECT_ROOT / "agent"

for path in (PROJECT_ROOT, AGENT_APP_ROOT, AGENTOS_SRC):
    value = str(path)
    if value not in sys.path:
        sys.path.insert(0, value)


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
