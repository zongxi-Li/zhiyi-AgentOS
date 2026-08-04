from __future__ import annotations

import asyncio
import json

from agentos.adapters.tool_adapter import register_tool_runtime_factory
from agentos.agents import AgentOutput, AgentProfile, AgentRegistry, BaseAgent
from agentos.core.acg import ACGBlueprint, ACGEdge, StepNode
from agentos.core.models.types import WorkflowDefinition, WorkflowStatus, WorkflowStepDefinition
from agentos.core.runtime import WorkflowRuntime
from agentos.core.workflow.progress import ProgressAssembler
from agentos.core.workflow.registry import WorkflowRegistry
from app.rag import LegalEvidenceRetriever
from app.tools.contracts import SourceReference, ToolExecutionRecord, ToolRunResult
from packs.legal.agents.contract_review_migration import LegalEvidenceMatchAgent
from packs.legal.agents.recovery import (
    LegalEvidenceRecoveryAgent,
    LegalEvidenceValidationAgent,
)


class _FixtureAgent(BaseAgent):
    def __init__(self, name: str, capability: str, output: dict):
        super().__init__(
            AgentProfile(agentName=name, domain="legal", capabilities=[capability])
        )
        self._output = output

    async def run(self, context):
        return AgentOutput(output=self._output)


class _LegalWebRuntime:
    def __init__(self, state=None, allowed_tools=None):
        self.state = state or {"calls": []}
        self.allowed_tools = set(
            allowed_tools
            if allowed_tools is not None
            else {"web_search", "current_datetime"}
        )

    @property
    def calls(self):
        return self.state["calls"]

    def scoped(self, allowed_tools):
        return _LegalWebRuntime(
            state=self.state,
            allowed_tools=self.allowed_tools.intersection(allowed_tools),
        )

    async def run(self, text, **kwargs):
        raise AssertionError("ACG recovery must use one-shot execute")

    async def execute(self, name, arguments, **kwargs):
        assert name in self.allowed_tools
        self.calls.append((name, dict(arguments)))
        source = SourceReference(
            citationId="src_legal_web",
            title="Public contract authority",
            url="https://example.test/legal-authority",
            snippet="Acceptance criteria should be objectively verifiable.",
            provider="web-fixture",
            retrievedAt="2026-08-04T00:00:00+00:00",
        )
        execution = ToolExecutionRecord(
            callId="call_legal_web",
            toolName=name,
            status="completed",
            durationMs=1,
            inputSummary="query",
            outputSummary="Found public contract authority.",
            sourceRefs=[source.citation_id],
        )
        return ToolRunResult(
            text=json.dumps({
                "ok": True,
                "tool": name,
                "data": {
                    "results": [{
                        "citationId": source.citation_id,
                        "title": source.title,
                        "url": source.url,
                        "snippet": source.snippet,
                        "score": 0.92,
                    }]
                },
            }),
            sources=[source],
            toolExecutions=[execution],
        )


def test_legal_evidence_gap_inserts_recovery_subgraph(monkeypatch):
    monkeypatch.setattr(LegalEvidenceRetriever, "retrieve", lambda self, **kwargs: [])
    tool_runtime = _LegalWebRuntime()
    register_tool_runtime_factory(lambda: tool_runtime)
    agents = AgentRegistry()
    for agent in [
        _FixtureAgent(
            "parser",
            "contract_parse",
            {"contract_type": "software development"},
        ),
        _FixtureAgent(
            "risk_detector",
            "risk_detect",
            {
                "risks": [
                    {
                        "id": "risk-001",
                        "title": "Missing acceptance baseline",
                        "level": "high",
                    }
                ]
            },
        ),
        LegalEvidenceMatchAgent(),
        LegalEvidenceRecoveryAgent(),
        LegalEvidenceValidationAgent(),
        _FixtureAgent("reporter", "report_generate", {"report_markdown": "# report"}),
    ]:
        agents.register(agent)

    workflow = WorkflowDefinition(
        workflowId="legal_dynamic_recovery_test",
        name="Legal dynamic recovery",
        domain="legal",
        intent="contract_review",
        runtimeEngine="acg",
        steps=[
            WorkflowStepDefinition(stepId="parse_contract", name="Parse", agentName="parser"),
            WorkflowStepDefinition(stepId="risk_detect", name="Risk", agentName="risk_detector"),
            WorkflowStepDefinition(
                stepId="legal_evidence_match",
                name="Evidence",
                agentName="legal_evidence_match",
                outputSpec={"type": "object", "required": ["evidences", "citations"]},
            ),
            WorkflowStepDefinition(stepId="report", name="Report", agentName="reporter"),
        ],
    )
    workflows = WorkflowRegistry()
    workflows.register(workflow)
    runtime = WorkflowRuntime(agent_registry=agents, workflow_registry=workflows)
    blueprint = ACGBlueprint(
        graphId="legal_dynamic_recovery_graph",
        nodes=[
            StepNode(nodeId="parse_contract", name="Parse", agentName="parser", capability="contract_parse"),
            StepNode(nodeId="risk_detect", name="Risk", agentName="risk_detector", capability="risk_detect"),
            StepNode(
                nodeId="legal_evidence_match",
                name="Evidence",
                agentName="legal_evidence_match",
                capability="legal_evidence_match",
            ),
            StepNode(nodeId="report", name="Report", agentName="reporter", capability="report_generate"),
        ],
        edges=[
            ACGEdge(edgeId="parse-risk", sourceId="parse_contract", targetId="risk_detect"),
            ACGEdge(edgeId="risk-evidence", sourceId="risk_detect", targetId="legal_evidence_match"),
            ACGEdge(edgeId="evidence-report", sourceId="legal_evidence_match", targetId="report"),
        ],
    )

    async def execute():
        task = runtime.create_task(
            title="Review a software agreement",
            domain="legal",
            intent="contract_review",
            input={
                "contractText": "Acceptance criteria are not defined.",
                "acgBlueprint": blueprint.model_dump(by_alias=True, mode="json"),
            },
        )
        return await runtime.start(task.task_id, workflow_id=workflow.workflow_id)

    run = asyncio.run(asyncio.wait_for(execute(), timeout=1.0))
    graph = run.runtime_graph
    assert run.status == WorkflowStatus.COMPLETED
    assert graph is not None
    assert graph.graph_version == 2
    assert len(graph.applied_patch_ids) == 1
    assert len([node for node in graph.nodes if node.created_graph_version == 2]) == 2
    assert len(graph.get_node("legal_evidence_match").attempts) == 2
    final_output = graph.get_node("legal_evidence_match").attempts[-1].output
    assert final_output["evidences"][0]["sourceType"] == "web"
    assert final_output["evidences"][0]["metadata"]["authoritativeSourceMissing"] is False
    assert final_output["evidences"][0]["metadata"]["url"] == "https://example.test/legal-authority"
    assert final_output["runtimeSignals"] == []
    assert [name for name, _ in tool_runtime.calls] == ["web_search"]
    tool_events = [event for event in run.trace if event.event_type.value == "tool_called"]
    assert len(tool_events) == 1
    assert tool_events[0].payload["sourceRefs"] == ["src_legal_web"]
    progress = ProgressAssembler().assemble(run)
    assert progress.dynamic_step_count == 2
