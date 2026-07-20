import asyncio

from fastapi import FastAPI
from fastapi.testclient import TestClient

from agentos.agents import AgentRegistry
from agentos.core.models.types import ReviewDecision, ReviewDecisionType, StepStatus, WorkflowStatus
from agentos.core.runtime import WorkflowRuntime
from agentos.core.workflow.registry import WorkflowRegistry
from app.api.agentos_core import create_router
from app.execution.runtime import configure_runtime
from app.llm.config import LLMConfig
from app.llm.gateway import LLMGateway, set_llm_gateway_for_tests
from packs.legal import register_pack as register_legal_pack


def _runtime() -> WorkflowRuntime:
    agents = AgentRegistry()
    workflows = WorkflowRegistry()
    register_legal_pack(agent_registry=agents, workflow_registry=workflows)
    return configure_runtime(WorkflowRuntime(agent_registry=agents, workflow_registry=workflows))


async def _start(runtime: WorkflowRuntime):
    task = runtime.create_task(
        title="合同审查",
        domain="legal",
        intent="contract_review",
        input={"source": "test", "contractText": "甲方委托乙方开发 CRM，签署后付款 30%，上线后付款 70%。"},
    )
    return await runtime.start(task.task_id, workflow_id="legal_contract_review_v1", review_mode="human_in_loop")


def test_canonical_contract_review_runs_on_acg_and_waits_for_review():
    async def run_test():
        run = await _start(runtime)
        assert run.workflow_id == "legal_contract_review_v1"
        assert run.runtime_engine == "acg"
        assert run.implementation_id == "legal_contract_review_v1"
        assert run.status == WorkflowStatus.WAITING_REVIEW
        assert run.current_step_id == "human_review"
        assert run.get_step("human_review").status == StepStatus.WAITING_REVIEW
        artifacts = run.output["artifacts"]
        assert artifacts["parse_contract"]["contract_type"]
        assert artifacts["risk_detect"]["risks"]
        assert artifacts["legal_evidence_match"]["evidences"]
        assert "suggestion_generate" in artifacts
        assert "report_generate" not in artifacts
        assert run.acg_blueprint is not None
        assert runtime.list_checkpoints(run.run_id)

    runtime = _runtime()
    asyncio.run(run_test())


def test_acg_contract_review_approve_reject_and_need_more_info():
    async def run_test():
        runtime = _runtime()
        waiting = await _start(runtime)
        more = await runtime.apply_review(ReviewDecision(
            runId=waiting.run_id, stepId="human_review", decision=ReviewDecisionType.NEED_MORE_INFO,
            reviewer="reviewer", comment="请补充验收附件",
        ))
        assert more.status == WorkflowStatus.WAITING_REVIEW
        rejected = await runtime.apply_review(ReviewDecision(
            runId=more.run_id, stepId="human_review", decision=ReviewDecisionType.REJECTED,
            reviewer="reviewer", comment="驳回",
        ))
        assert rejected.status == WorkflowStatus.FAILED

        approved_waiting = await _start(runtime)
        completed = await runtime.apply_review(ReviewDecision(
            runId=approved_waiting.run_id, stepId="human_review", decision=ReviewDecisionType.APPROVED,
            reviewer="reviewer", comment="通过",
        ))
        assert completed.status == WorkflowStatus.COMPLETED
        assert completed.get_step("report_generate").status == StepStatus.COMPLETED
        artifacts = completed.output["artifacts"]
        report = artifacts["report_generate"]["report_markdown"]
        assert report
        assert "本报告不构成最终法律意见" in report
        assert "Evidence 依据链" in report
        assert "审核意见：通过" in report
        assert artifacts["risk_detect"]["risks"]
        assert artifacts["legal_evidence_match"]["evidences"]

    asyncio.run(run_test())


class _InvalidJSONProvider:
    provider_name = "invalid-json"
    model = "invalid-json"

    def generate_text(self, prompt: str, **kwargs):
        return "invalid"

    def generate_json(self, prompt: str, schema: dict, **kwargs):
        return {"invalid": True}


def test_acg_contract_review_invalid_llm_json_uses_fallback():
    async def run_test():
        run = await _start(_runtime())
        parse = run.output["artifacts"]["parse_contract"]
        risks = run.output["artifacts"]["risk_detect"]
        assert parse["contract_type"]
        assert risks["risks"]
        assert parse["_llm"]["source"] == "mock_fallback"
        assert risks["_llm"]["source"] == "mock_fallback"

    set_llm_gateway_for_tests(LLMGateway(provider=_InvalidJSONProvider()))
    try:
        asyncio.run(run_test())
    finally:
        set_llm_gateway_for_tests(None)


def test_acg_contract_review_evidence_fallback_covers_partial_retrieval_failure(monkeypatch):
    from packs.legal.agents import contract_review_migration as migration

    class _PartialFailureRetriever:
        def __init__(self):
            self.calls = 0

        def retrieve(self, *, risk, contract_type, top_k):
            self.calls += 1
            if self.calls == 1:
                return [{
                    "id": "ev-live-01",
                    "stepId": "legal_evidence_match",
                    "riskId": str(risk.get("id") or ""),
                    "sourceType": "law",
                    "sourceName": "测试法律知识库",
                    "content": "测试依据",
                    "citationText": "第一项风险的真实检索依据。",
                    "confidence": 0.9,
                }]
            raise RuntimeError("partial retrieval failure")

    monkeypatch.setattr(migration, "LegalEvidenceRetriever", _PartialFailureRetriever)
    set_llm_gateway_for_tests(LLMGateway(provider=_InvalidJSONProvider()))
    try:
        run = asyncio.run(_start(_runtime()))
    finally:
        set_llm_gateway_for_tests(None)

    risks = run.output["artifacts"]["risk_detect"]["risks"]
    evidence_output = run.output["artifacts"]["legal_evidence_match"]
    covered_risk_ids = {item.get("riskId") for item in evidence_output["evidences"]}
    assert {item["id"] for item in risks}.issubset(covered_risk_ids)
    assert evidence_output["retrieval"]["fallback"] is True
    assert len(evidence_output["retrieval"]["errors"]) == 2


def test_acg_contract_review_api_trace_checkpoint_and_metrics():
    runtime = _runtime()
    app = FastAPI()
    app.include_router(create_router(runtime), prefix="/ai")
    client = TestClient(app)
    started = client.post("/ai/core/workflows/start", json={
        "title": "合同审查", "domain": "legal", "intent": "contract_review",
        "workflowId": "legal_contract_review_v1", "reviewMode": "human_in_loop",
        "input": {"contractText": "甲方委托乙方开发 CRM。"},
    }).json()["run"]
    assert started["runtimeEngine"] == "acg"
    assert "implementationId" in started
    run_id = started["runId"]
    assert client.get(f"/ai/core/workflows/runs/{run_id}/trace").json()["workflowId"] == "legal_contract_review_v1"
    assert client.get(f"/ai/core/workflows/runs/{run_id}/checkpoints").json()["total"] >= 1
    view = client.get(f"/ai/core/workflows/runs/{run_id}/acg").json()
    assert view["engine"] == "acg"
    assert view["acgBlueprint"]["nodes"]
    assert client.get("/ai/core/workflows/metrics", params={"workflowId": "legal_contract_review_v1"}).json()["workflowId"] == "legal_contract_review_v1"


def test_llm_gateway_without_configuration_uses_mock():
    gateway = LLMGateway(config=LLMConfig(provider="openai-compatible", base_url="", api_key="", model=""))
    assert gateway.provider_name == "mock"
