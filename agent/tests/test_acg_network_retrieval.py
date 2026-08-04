from __future__ import annotations

import asyncio
import json

from agentos.adapters.tool_adapter import register_tool_runtime_factory
from agentos.agents import AgentRegistry
from agentos.core.acg import ACGBlueprint, StepNode
from agentos.core.models.types import WorkflowDefinition, WorkflowStatus, WorkflowStepDefinition
from agentos.core.native import NativeGeneralAgent
from agentos.core.runtime import WorkflowRuntime
from agentos.core.workflow.registry import WorkflowRegistry
from app.tools.contracts import SourceReference, ToolExecutionRecord, ToolRunResult
from packs.legal.agents.statute import StatuteAgent


class _TrackingToolRuntime:
    def __init__(self, *, hang_web: bool = False, state=None, allowed_tools=None):
        self.hang_web = hang_web
        self.state = state or {"calls": [], "cancelled": asyncio.Event(), "run_calls": 0}
        self.allowed_tools = set(
            allowed_tools
            if allowed_tools is not None
            else {"web_search", "knowledge_search", "current_datetime"}
        )

    @property
    def calls(self):
        return self.state["calls"]

    @property
    def cancelled(self):
        return self.state["cancelled"]

    def scoped(self, allowed_tools):
        return _TrackingToolRuntime(
            hang_web=self.hang_web,
            state=self.state,
            allowed_tools=self.allowed_tools.intersection(allowed_tools),
        )

    async def run(self, text, **kwargs):
        self.state["run_calls"] += 1
        raise AssertionError("ACG must not enter the model-driven tool loop")

    async def execute(self, name, arguments, **kwargs):
        if name not in self.allowed_tools:
            raise PermissionError(f"tool not allowed: {name}")
        self.calls.append((name, dict(arguments)))
        if name == "web_search" and self.hang_web:
            try:
                await asyncio.Event().wait()
            finally:
                self.cancelled.set()
        is_web = name == "web_search"
        source = SourceReference(
            citationId="src_web_fixture" if is_web else "src_local_fixture",
            title="Current public authority" if is_web else "Local knowledge authority",
            url="https://example.test/current-authority" if is_web else None,
            snippet="Current public legal and implementation evidence.",
            provider="web-fixture" if is_web else "knowledge-fixture",
            retrievedAt="2026-08-04T00:00:00+00:00",
        )
        record = ToolExecutionRecord(
            callId=f"call_{name}",
            toolName=name,
            status="completed",
            durationMs=1,
            inputSummary="query",
            outputSummary="Found deterministic evidence.",
            sourceRefs=[source.citation_id],
        )
        payload = {
            "ok": True,
            "tool": name,
            "data": {
                "results": [{
                    "citationId": source.citation_id,
                    "title": source.title,
                    "url": source.url,
                    "snippet": source.snippet,
                    "score": 0.95,
                }]
            },
        }
        return ToolRunResult(
            text=json.dumps(payload),
            sources=[source],
            toolExecutions=[record],
        )


async def _run_single_retrieval(
    *,
    agent,
    domain: str,
    capability: str,
    task_input: dict,
    tool_runtime: _TrackingToolRuntime,
    tool_timeout: float = 0.2,
):
    register_tool_runtime_factory(lambda: tool_runtime)
    agents = AgentRegistry()
    agents.register(agent)
    workflow = WorkflowDefinition(
        workflowId=f"{domain}_{capability}_network_test",
        name="Network retrieval test",
        domain=domain,
        intent="research",
        runtimeEngine="acg",
        steps=[
            WorkflowStepDefinition(
                stepId="retrieve",
                name="Retrieve",
                agentName=agent.profile.agent_name,
                capability=capability,
                timeout=1,
            )
        ],
    )
    workflows = WorkflowRegistry()
    workflows.register(workflow)
    runtime = WorkflowRuntime(agent_registry=agents, workflow_registry=workflows)
    runtime.orchestrator.tool_timeout_seconds = tool_timeout
    blueprint = ACGBlueprint(
        graphId=f"{domain}_{capability}_network_graph",
        nodes=[
            StepNode(
                nodeId="retrieve",
                name="Retrieve",
                agentName=agent.profile.agent_name,
                capability=capability,
                timeout=1,
            )
        ],
        edges=[],
    )
    task = runtime.create_task(
        title="Retrieve current source-backed information",
        domain=domain,
        intent="research",
        input={
            **task_input,
            "webSearchEnabled": True,
            "acgBlueprint": blueprint.model_dump(by_alias=True, mode="json"),
        },
    )
    return await asyncio.wait_for(
        runtime.start(task.task_id, workflow_id=workflow.workflow_id),
        timeout=1.0,
    )


def _tool_events(run):
    return [event for event in run.trace if event.event_type.value == "tool_called"]


def test_native_acg_uses_one_shot_web_search_and_preserves_citations():
    tool_runtime = _TrackingToolRuntime()

    run = asyncio.run(
        _run_single_retrieval(
            agent=NativeGeneralAgent(),
            domain="general",
            capability="information_retrieval",
            task_input={"userIntent": "Research the latest ACG implementation evidence"},
            tool_runtime=tool_runtime,
        )
    )

    assert run.status == WorkflowStatus.COMPLETED
    assert [name for name, _ in tool_runtime.calls] == ["web_search"]
    assert tool_runtime.state["run_calls"] == 0
    assert tool_runtime.calls[0][1]["max_results"] == 5
    output = run.steps[0].output
    assert output["retrieval_mode"] == "web_search"
    assert output["evidence_refs"] == ["src_web_fixture"]
    assert output["sources"][0]["url"] == "https://example.test/current-authority"
    assert _tool_events(run)[0].payload["toolName"] == "web_search"


def test_legal_statute_acg_uses_bounded_web_search():
    tool_runtime = _TrackingToolRuntime()

    run = asyncio.run(
        _run_single_retrieval(
            agent=StatuteAgent(),
            domain="legal",
            capability="statute_retrieval",
            task_input={"caseText": "查询当前软件合同验收规则"},
            tool_runtime=tool_runtime,
        )
    )

    assert run.status == WorkflowStatus.COMPLETED
    assert [name for name, _ in tool_runtime.calls] == ["web_search"]
    assert run.steps[0].output["retrieval_mode"] == "web_search"
    assert run.steps[0].output["evidence_refs"] == ["src_web_fixture"]
    assert _tool_events(run)[0].payload["status"] == "completed"


def test_hanging_web_search_is_cancelled_and_falls_back_without_blocking_run():
    tool_runtime = _TrackingToolRuntime(hang_web=True)

    run = asyncio.run(
        _run_single_retrieval(
            agent=NativeGeneralAgent(),
            domain="general",
            capability="information_retrieval",
            task_input={"userIntent": "Research current information"},
            tool_runtime=tool_runtime,
            tool_timeout=0.01,
        )
    )

    assert run.status == WorkflowStatus.COMPLETED
    assert [name for name, _ in tool_runtime.calls] == [
        "web_search",
        "knowledge_search",
    ]
    assert tool_runtime.cancelled.is_set()
    assert run.steps[0].output["retrieval_mode"] == "local_knowledge"
    events = _tool_events(run)
    assert [(item.payload["toolName"], item.payload["status"]) for item in events] == [
        ("web_search", "failed"),
        ("knowledge_search", "completed"),
    ]
    assert events[0].payload["errorCode"] == "TOOL_TIMEOUT"
    assert run.active_step_ids == []
    assert run.runtime_graph is not None
    assert run.runtime_graph.get_node("retrieve").attempts[-1].ended_at is not None
