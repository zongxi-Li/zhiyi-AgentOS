import asyncio
import inspect
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
AGENTOS_SRC = PROJECT_ROOT / "agentOS" / "src"
AGENT_APP_ROOT = PROJECT_ROOT / "agent"

for path in (PROJECT_ROOT, AGENT_APP_ROOT, AGENTOS_SRC):
    value = str(path)
    if value not in sys.path:
        sys.path.insert(0, value)


@pytest.fixture(autouse=True)
def _force_mock_llm(monkeypatch):
    """默认让所有测试走 mock LLM，保证稳定、零成本、零网络。

    生产环境通过 .env 的 DEEPSEEK_*/DASHSCOPE_* 自动接通真实模型；
    但测试不应依赖外部 API。显式置 AGENTOS_LLM_PROVIDER=mock 可覆盖
    config.from_env 的供应商回落映射；需要真实 provider 行为的个别
    测试仍可用 set_llm_gateway_for_tests 注入自定义 provider。
    """
    monkeypatch.setenv("AGENTOS_LLM_PROVIDER", "mock")


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
