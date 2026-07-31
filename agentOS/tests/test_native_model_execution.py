from __future__ import annotations

import asyncio

from agentos.adapters.model_adapter import StructuredGenerationResult
from agentos.agents.base import AgentRunContext
from agentos.core.models.types import (
    AgentTask,
    WorkflowDefinition,
    WorkflowRun,
    WorkflowStep,
)
from agentos.core.native import NativeGeneralAgent
from agentos.core.planning.default_catalog import build_default_capability_catalog
from agentos.memory.workflow_memory import WorkflowMemory


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
