import asyncio
import json
from types import SimpleNamespace

import pytest

from agentos.adapters.tool_adapter import (
    BoundedToolRuntime,
    network_tools_enabled,
    register_tool_runtime_factory,
)
from agentos.agents.base import AgentOutput, AgentProfile, BaseAgent
from agentos.agents.registry import AgentRegistry
from agentos.core.models.types import (
    AgentTask,
    WorkflowDefinition,
    WorkflowRun,
    WorkflowStep,
)
from agentos.core.native import NativeGeneralAgent
from agentos.core.workflow.orchestrator import Orchestrator
from agentos.memory.workflow_memory import WorkflowMemory


class _RecordingRuntime:
    def __init__(self):
        self.scoped_tools = None
        self.calls = []

    def scoped(self, allowed_tools):
        self.scoped_tools = frozenset(allowed_tools)
        return self

    async def execute(self, name, arguments, **kwargs):
        self.calls.append((name, arguments))
        return SimpleNamespace(
            text=json.dumps({"ok": True, "tool": name, "data": {"results": []}}),
            sources=[],
            tool_executions=[],
        )


class _CapturingAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            AgentProfile(
                agentName="capturing_agent",
                domain="general",
                capabilities=["capture"],
                allowedTools=[
                    "web_search",
                    "web_extract",
                    "knowledge_search",
                    "current_datetime",
                ],
            )
        )
        self.runtime = None

    async def run(self, context):
        self.runtime = context.tool_runtime
        return AgentOutput(output={"captured": True}, summary="captured")


@pytest.mark.parametrize("value", [False, 0, "0", "false", "off", "disabled", "no"])
def test_network_policy_accepts_explicit_boolean_like_opt_outs(value):
    assert network_tools_enabled({"webSearchEnabled": value}) is False


async def test_acg_orchestrator_scopes_exact_declared_read_only_tools():
    runtime = _RecordingRuntime()
    register_tool_runtime_factory(lambda: runtime)
    agent = _CapturingAgent()
    registry = AgentRegistry()
    registry.register(agent)
    orchestrator = Orchestrator(registry)
    task = AgentTask(title="online ACG")
    workflow = WorkflowDefinition(
        workflowId="offline-acg",
        name="Offline ACG",
        domain="general",
        intent="general",
        runtimeEngine="acg",
        steps=[],
    )
    run = WorkflowRun(
        taskId=task.task_id,
        workflowId=workflow.workflow_id,
        domain="general",
        runtimeEngine="acg",
    )
    step = WorkflowStep(
        stepId="capture",
        name="Capture",
        agentName=agent.profile.agent_name,
        capability="capture",
    )

    await orchestrator.dispatch_agent(
        task=task,
        run=run,
        workflow=workflow,
        step=step,
        memory=WorkflowMemory(run_id=run.run_id, task_input={}),
    )

    assert runtime.scoped_tools == frozenset({
        "web_search",
        "web_extract",
        "knowledge_search",
        "current_datetime",
    })
    assert isinstance(agent.runtime, BoundedToolRuntime)
    assert agent.runtime.delegate is runtime


async def test_acg_explicit_network_opt_out_removes_only_network_tools():
    runtime = _RecordingRuntime()
    register_tool_runtime_factory(lambda: runtime)
    agent = _CapturingAgent()
    registry = AgentRegistry()
    registry.register(agent)
    task = AgentTask(title="private ACG", input={"webSearchEnabled": False})
    workflow = WorkflowDefinition(
        workflowId="private-acg",
        name="Private ACG",
        domain="general",
        intent="general",
        runtimeEngine="acg",
        steps=[],
    )
    run = WorkflowRun(
        taskId=task.task_id,
        workflowId=workflow.workflow_id,
        domain="general",
        runtimeEngine="acg",
    )
    step = WorkflowStep(
        stepId="capture",
        name="Capture",
        agentName=agent.profile.agent_name,
        capability="capture",
    )

    await Orchestrator(registry).dispatch_agent(
        task=task,
        run=run,
        workflow=workflow,
        step=step,
        memory=WorkflowMemory(run_id=run.run_id, task_input=task.input),
    )

    assert runtime.scoped_tools == frozenset({"knowledge_search", "current_datetime"})


def test_native_acg_profile_advertises_bounded_web_search():
    assert set(NativeGeneralAgent().profile.allowed_tools) == {
        "web_search",
        "knowledge_search",
        "current_datetime",
    }


async def test_native_offline_retrieval_uses_one_local_call_and_task_input_fallback():
    runtime = _RecordingRuntime()
    register_tool_runtime_factory(lambda: runtime)
    agent = NativeGeneralAgent()
    registry = AgentRegistry()
    registry.register(agent)
    task = AgentTask(
        title="offline evidence",
        input={
            "userIntent": "Use the supplied production figures only.",
            "webSearchEnabled": False,
        },
    )
    workflow = WorkflowDefinition(
        workflowId="offline-retrieval",
        name="Offline retrieval",
        domain="general",
        intent="general",
        runtimeEngine="acg",
        steps=[],
    )
    run = WorkflowRun(
        taskId=task.task_id,
        workflowId=workflow.workflow_id,
        domain="general",
        runtimeEngine="acg",
    )
    step = WorkflowStep(
        stepId="retrieve",
        name="Retrieve",
        agentName=agent.profile.agent_name,
        capability="information_retrieval",
    )

    output, _ = await Orchestrator(registry).dispatch_agent(
        task=task,
        run=run,
        workflow=workflow,
        step=step,
        memory=WorkflowMemory(run_id=run.run_id, task_input=task.input),
    )

    assert [name for name, _ in runtime.calls] == ["knowledge_search"]
    assert output.output["retrieval_mode"] == "task_input_only"
    assert output.sources[0]["provider"] == "task-input"
    assert output.evidence_refs == [output.sources[0]["citationId"]]


async def test_bounded_tool_runtime_cancels_a_hanging_provider_without_blocking():
    cancelled = asyncio.Event()

    class _HangingRuntime(_RecordingRuntime):
        async def execute(self, name, arguments, **kwargs):
            try:
                await asyncio.Event().wait()
            finally:
                cancelled.set()

    bounded = BoundedToolRuntime(_HangingRuntime(), timeout_seconds=0.01)

    with pytest.raises(TimeoutError):
        await asyncio.wait_for(
            bounded.execute("web_search", {"query": "latest law"}),
            timeout=0.2,
        )

    assert cancelled.is_set()
