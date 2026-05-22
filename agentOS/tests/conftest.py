import asyncio
import inspect
import sys
from pathlib import Path


AGENTOS_ROOT = Path(__file__).resolve().parents[1]
AGENTOS_SRC = AGENTOS_ROOT / "src"

value = str(AGENTOS_SRC)
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
