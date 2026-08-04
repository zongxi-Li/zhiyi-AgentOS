from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace

from agentos.adapters.tool_adapter import register_tool_runtime_factory
from agentos.agents import AgentOutput, AgentProfile, AgentRegistry, BaseAgent
from agentos.core.acg import ACGBlueprint, ACGEdge, StepNode
from agentos.core.models.types import WorkflowDefinition, WorkflowStatus, WorkflowStepDefinition
from agentos.core.native import NativeGeneralAgent
from agentos.core.runtime import WorkflowRuntime
from agentos.core.workflow.progress import ProgressAssembler
from agentos.core.workflow.registry import WorkflowRegistry


class _EmptyKnowledgeRuntime:
    def scoped(self, allowed_tools):
        return self

    async def execute(self, name, arguments, **kwargs):
        return SimpleNamespace(
            text=json.dumps({"ok": True, "tool": name, "data": {"results": []}}),
            sources=[],
            tool_executions=[],
        )


class _ReportAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            AgentProfile(
                agentName="native_report_fixture",
                domain="general",
                capabilities=["artifact_generation"],
            )
        )

    async def run(self, context):
        return AgentOutput(output={"final_answer": "# complete"})


def test_native_missing_source_inserts_recovery_subgraph():
    register_tool_runtime_factory(_EmptyKnowledgeRuntime)
    agents = AgentRegistry()
    agents.register(NativeGeneralAgent())
    agents.register(_ReportAgent())
    workflow = WorkflowDefinition(
        workflowId="native_dynamic_recovery_test",
        name="Native dynamic recovery",
        domain="general",
        intent="research",
        runtimeEngine="acg",
        steps=[
            WorkflowStepDefinition(
                stepId="retrieve",
                name="Retrieve",
                agentName="native_general_agent",
                capability="information_retrieval",
                outputSpec={
                    "type": "object",
                    "required": ["retrieved_information", "evidence_refs"],
                },
            ),
            WorkflowStepDefinition(
                stepId="report",
                name="Report",
                agentName="native_report_fixture",
                capability="artifact_generation",
            ),
        ],
    )
    workflows = WorkflowRegistry()
    workflows.register(workflow)
    runtime = WorkflowRuntime(agent_registry=agents, workflow_registry=workflows)
    blueprint = ACGBlueprint(
        graphId="native_dynamic_recovery_graph",
        nodes=[
            StepNode(
                nodeId="retrieve",
                name="Retrieve",
                agentName="native_general_agent",
                capability="information_retrieval",
            ),
            StepNode(
                nodeId="report",
                name="Report",
                agentName="native_report_fixture",
                capability="artifact_generation",
            ),
        ],
        edges=[ACGEdge(edgeId="retrieve-report", sourceId="retrieve", targetId="report")],
    )

    async def execute():
        task = runtime.create_task(
            title="Research a source-backed implementation plan",
            domain="general",
            intent="research",
            input={
                "userIntent": "Research a source-backed implementation plan",
                "acgBlueprint": blueprint.model_dump(by_alias=True, mode="json"),
            },
        )
        return await runtime.start(task.task_id, workflow_id=workflow.workflow_id)

    run = asyncio.run(execute())
    graph = run.runtime_graph
    assert run.status == WorkflowStatus.COMPLETED
    assert graph is not None
    assert graph.graph_version == 2
    assert len(graph.applied_patch_ids) == 1
    assert len([node for node in graph.nodes if node.created_graph_version == 2]) == 2
    target = graph.get_node("retrieve")
    assert len(target.attempts) == 2
    assert target.attempts[-1].output["retrieval_mode"] == "recovered_task_input"
    assert target.attempts[-1].output["runtimeSignals"] == []
    progress = ProgressAssembler().assemble(run)
    assert progress.dynamic_step_count == 2

