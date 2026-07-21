import asyncio
import inspect
import os
import sys
import tempfile
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
AGENTOS_SRC = PROJECT_ROOT / "agentOS" / "src"
AGENT_APP_ROOT = PROJECT_ROOT / "agent"

# AgentOS creates its global Chroma client while test modules are imported.
# Isolate that client before collection so tests never open the tracked database.
_TEST_CHROMA_DIR = tempfile.TemporaryDirectory(prefix="kinlin-agent-chroma-tests-")
os.environ["AGENT_CHROMA_PATH"] = _TEST_CHROMA_DIR.name

for path in (PROJECT_ROOT, AGENT_APP_ROOT, AGENTOS_SRC):
    value = str(path)
    if value not in sys.path:
        sys.path.insert(0, value)


class _ContractReviewTestProvider:
    """Deterministic business fixtures kept outside the application package."""

    provider_name = "test-fixture"
    model = "contract-review-fixture"

    def generate_text(self, prompt, **kwargs):
        return ""

    def generate_json(self, prompt, schema, **kwargs):
        from app.llm.schemas import compact_schema_name

        task = compact_schema_name(schema)
        if task == "parse_contract":
            return {
                "contract_title": "测试合同",
                "parties": [
                    {"name": "甲方", "role": "委托方"},
                    {"name": "乙方", "role": "服务方"},
                ],
                "contract_type": "测试服务合同",
                "key_dates": [],
                "amounts": [],
                "obligations": [],
                "summary": "测试输入中的合同内容。",
                "scope": "测试服务范围",
                "payment_terms": "测试付款安排",
                "acceptance_terms": "测试验收安排",
                "ip_terms": "",
                "dispute_resolution": "",
            }
        if task == "risk_detect":
            return {
                "risks": [{
                    "id": "risk-test-payment",
                    "title": "付款安排需要复核",
                    "level": "high",
                    "clause": "测试付款安排",
                    "reason": "测试输入中的付款触发条件需要进一步核对。",
                    "consequence": "付款条件不清可能导致履约争议。",
                    "suggestion": "结合交付与验收节点复核付款条件。",
                    "evidenceIds": [],
                }]
            }
        if task == "report_generate":
            return {"report_markdown": "# 测试合同审查报告\n\n报告内容来自测试夹具。"}
        return {}


@pytest.fixture(autouse=True)
def _force_mock_llm(monkeypatch):
    """默认让所有测试走 mock LLM，保证稳定、零成本、零网络。

    生产环境通过 .env 的 DEEPSEEK_*/DASHSCOPE_* 自动接通真实模型；
    但测试不应依赖外部 API。显式置 AGENTOS_LLM_PROVIDER=mock 可覆盖
    config.from_env 的供应商回落映射；需要真实 provider 行为的个别
    测试仍可用 set_llm_gateway_for_tests 注入自定义 provider。
    """
    monkeypatch.setenv("AGENTOS_LLM_PROVIDER", "mock")
    from app.llm.gateway import LLMGateway, set_llm_gateway_for_tests

    set_llm_gateway_for_tests(LLMGateway(provider=_ContractReviewTestProvider()))
    yield
    set_llm_gateway_for_tests(None)


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


def pytest_unconfigure(config):
    chroma_module = sys.modules.get("agentos.adapters.retrieval.chroma_client")
    if chroma_module is not None:
        client = getattr(chroma_module.chroma_legal_client, "client", None)
        close = getattr(client, "close", None)
        if callable(close):
            close()
    _TEST_CHROMA_DIR.cleanup()
