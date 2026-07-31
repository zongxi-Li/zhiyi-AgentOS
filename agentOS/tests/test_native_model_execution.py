from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from agentos.adapters.model_adapter import (
    StructuredGenerationError,
    StructuredGenerationResult,
)
from agentos.agents import AgentRegistry
from agentos.agents.base import AgentRunContext
from agentos.core.models.types import (
    AgentTask,
    WorkflowDefinition,
    WorkflowRun,
    WorkflowStatus,
    WorkflowStep,
)
from agentos.core.native import NativeGeneralAgent
from agentos.core.planning.default_catalog import build_default_capability_catalog
from agentos.memory.workflow_memory import WorkflowMemory
from agentos.core.workflow.orchestrator import Orchestrator


class _RepairRuntime:
    def __init__(self, valid_runtime):
        self.valid_runtime = valid_runtime
        self.calls = 0

    def is_available(self):
        return True

    async def generate_json(self, **kwargs):
        self.calls += 1
        if self.calls == 1:
            return StructuredGenerationResult(
                data={"task_summary": "incomplete"},
                provider="test-provider",
                model="test-model",
                promptVersion=kwargs["prompt_version"],
            )
        return await self.valid_runtime.generate_json(**kwargs)


class _JsonRepairRuntime:
    def __init__(self, valid_runtime, *, invalid_after_retry=False):
        self.valid_runtime = valid_runtime
        self.invalid_after_retry = invalid_after_retry
        self.calls = []

    def is_available(self):
        return True

    async def generate_json(self, **kwargs):
        self.calls.append(kwargs)
        if len(self.calls) == 1:
            raise StructuredGenerationError(
                "MODEL_OUTPUT_INVALID_JSON",
                "Invalid JSON returned by provider: Unterminated string",
            )
        if self.invalid_after_retry:
            return StructuredGenerationResult(
                data={"task_summary": "still incomplete"},
                provider="test-provider",
                model="test-model",
                promptVersion=kwargs["prompt_version"],
            )
        return await self.valid_runtime.generate_json(**kwargs)


def _context(model_runtime, *, objective="Design a measurable delivery plan"):
    catalog = build_default_capability_catalog()
    descriptor = catalog.get("task_understanding")
    task = AgentTask(
        title=objective,
        input={"userIntent": objective, "thinkingMode": "disabled"},
    )
    run = WorkflowRun(
        taskId=task.task_id,
        workflowId="native_test",
        domain="general",
        runtimeEngine="acg",
        input=dict(task.input),
    )
    workflow = WorkflowDefinition(
        workflowId="native_test",
        name="Native test",
        domain="general",
        intent="general",
        runtimeEngine="acg",
        steps=[],
        definitionType="native_bootstrap",
    )
    step = WorkflowStep(
        stepId="understand",
        name="Understand the task",
        agentName="native_general_agent",
        capability="task_understanding",
        outputSpec=descriptor.output_contract,
    )
    return AgentRunContext(
        task=task,
        run=run,
        workflow=workflow,
        step=step,
        memory=WorkflowMemory(run_id=run.run_id, task_input=dict(task.input)),
        modelRuntime=model_runtime,
        capabilityDescriptor=descriptor,
    )


def test_native_agent_repairs_invalid_structured_output_once(structured_model_runtime):
    runtime = _RepairRuntime(structured_model_runtime)

    result = asyncio.run(NativeGeneralAgent().run(_context(runtime)))

    assert runtime.calls == 2
    assert len(result.model_invocations) == 2
    assert result.output["constraints"]


def test_native_prompt_is_input_sensitive_and_domain_neutral(structured_model_runtime):
    agent = NativeGeneralAgent()

    asyncio.run(agent.run(_context(structured_model_runtime, objective="Plan alpha")))
    asyncio.run(agent.run(_context(structured_model_runtime, objective="Plan beta")))

    prompts = [item["prompt"] for item in structured_model_runtime.calls]
    assert "Plan alpha" in prompts[0]
    assert "Plan beta" in prompts[1]
    assert all("industrial_graph" not in prompt for prompt in prompts)
    assert all("software_graph" not in prompt for prompt in prompts)


def test_native_prompt_deduplicates_workbench_task_text(structured_model_runtime):
    objective = "Unique canonical objective with measurable constraints"
    context = _context(structured_model_runtime, objective=objective)
    context.task.input.update({"taskGoal": objective, "materialText": objective})

    asyncio.run(NativeGeneralAgent().run(context))

    prompt = structured_model_runtime.calls[-1]["prompt"]
    assert prompt.count(objective) == 1
    assert "authenticatedUserId" not in prompt


def test_native_agent_repairs_truncated_json_once(structured_model_runtime):
    runtime = _JsonRepairRuntime(structured_model_runtime)

    result = asyncio.run(NativeGeneralAgent().run(_context(runtime)))

    assert len(runtime.calls) == 2
    assert runtime.calls[-1]["prompt_version"].endswith(".json-repair1")
    assert "smaller response" in runtime.calls[-1]["prompt"]
    assert result.output["constraints"]


def test_native_agent_never_uses_more_than_one_repair(structured_model_runtime):
    runtime = _JsonRepairRuntime(structured_model_runtime, invalid_after_retry=True)

    with pytest.raises(StructuredGenerationError) as raised:
        asyncio.run(NativeGeneralAgent().run(_context(runtime)))

    assert raised.value.code == "OUTPUT_CONTRACT_VIOLATION"
    assert len(runtime.calls) == 2


def test_native_analysis_contract_bounds_response_shape():
    schema = build_default_capability_catalog().get("analysis").output_contract
    properties = schema["properties"]["analysis"]["properties"]

    assert properties["findings"]["maxItems"] == 8
    assert properties["findings"]["items"]["maxLength"] == 400
    assert properties["assumptions"]["maxItems"] == 8
    assert properties["gaps"]["maxItems"] == 8


def test_failed_run_has_partial_artifacts_but_no_completion_message():
    run = WorkflowRun(
        taskId="task_failed",
        workflowId="native_test",
        domain="general",
        runtimeEngine="acg",
        status=WorkflowStatus.FAILED,
        steps=[
            WorkflowStep(
                stepId="understand",
                name="Task understanding",
                agentName="native_general_agent",
                status="completed",
                output={"task_summary": "partial"},
            )
        ],
    )

    output = Orchestrator(AgentRegistry()).compose_final_output(run)

    assert "final_answer" not in output
    assert output["artifacts"] == {"understand": {"task_summary": "partial"}}


def test_artifact_generation_consumes_all_upstream_and_normalizes_envelope(
    structured_model_runtime,
):
    catalog = build_default_capability_catalog()
    descriptor = catalog.get("artifact_generation")
    task = AgentTask(
        title="Factory delivery plan",
        input={"userIntent": "Produce one complete delivery plan"},
    )
    run = WorkflowRun(
        runId="run_artifact",
        taskId=task.task_id,
        workflowId="native_test",
        domain="general",
        runtimeEngine="acg",
        input=dict(task.input),
    )
    workflow = WorkflowDefinition(
        workflowId="native_test",
        name="Native test",
        domain="general",
        intent="general",
        runtimeEngine="acg",
        steps=[],
        definitionType="native_bootstrap",
    )
    step = WorkflowStep(
        stepId="deliver",
        name="Compose final artifact",
        agentName="native_general_agent",
        capability="artifact_generation",
        outputSpec=descriptor.output_contract,
        attempt=2,
    )
    upstream = {
        "task_summary": "Build a production line",
        "requirements": [{"id": "R1"}],
        "acceptance_criteria": [{"target": "55 seconds"}],
        "capacity_plan": {"conclusion": "240000 units/year"},
        "cost_analysis": {"total": 8000000},
        "risks": [{"risk": "schedule"}],
        "verification": {"status": "partial"},
    }
    context = AgentRunContext(
        task=task,
        run=run,
        workflow=workflow,
        step=step,
        memory=WorkflowMemory(run_id=run.run_id, task_input=dict(task.input)),
        contextPack=SimpleNamespace(
            data=upstream,
            source_data={"upstream": upstream},
            evidence_refs=["source-1"],
        ),
        modelRuntime=structured_model_runtime,
        capabilityDescriptor=descriptor,
    )

    result = asyncio.run(NativeGeneralAgent().run(context))

    prompt = structured_model_runtime.calls[-1]["prompt"]
    for field in upstream:
        assert field in prompt
    assert "consumeAllRelevantUpstreamFields" in prompt
    assert result.output["artifact"] == {
        "artifactId": "artifact_52676df0e94b2d89",
        "type": "report",
        "title": "generated:title",
        "mediaType": "text/markdown",
        "content": "generated:final_answer",
        "structuredData": result.output["deliverable"],
    }
    assert result.output["verification"]["status"] == "passed"
