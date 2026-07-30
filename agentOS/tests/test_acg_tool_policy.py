from agentos.adapters.tool_adapter import register_tool_runtime_factory
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

    def scoped(self, allowed_tools):
        self.scoped_tools = frozenset(allowed_tools)
        return self


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


async def test_acg_orchestrator_blocks_network_tools_even_if_agent_requests_them():
    runtime = _RecordingRuntime()
    register_tool_runtime_factory(lambda: runtime)
    agent = _CapturingAgent()
    registry = AgentRegistry()
    registry.register(agent)
    orchestrator = Orchestrator(registry)
    task = AgentTask(title="offline ACG")
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

    assert runtime.scoped_tools == frozenset(
        {"knowledge_search", "current_datetime"}
    )
    assert agent.runtime is runtime


def test_native_acg_profile_does_not_advertise_network_tools():
    assert set(NativeGeneralAgent().profile.allowed_tools) == {
        "knowledge_search",
        "current_datetime",
    }
