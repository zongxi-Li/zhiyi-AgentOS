from __future__ import annotations

import asyncio

import pytest

from agentos.agents import AgentOutput, AgentProfile, AgentRegistry, BaseAgent
from agentos.core.acg import ControlNode, ControlType
from agentos.core.models.types import WorkflowDefinition, WorkflowStatus, WorkflowStepDefinition
from agentos.core.planning import ACGBuilder, TaskSemanticProfile
from agentos.core.planning.cognitive_router import CapabilityBinding, CollaborationNetwork
from agentos.core.runtime import WorkflowRuntime
from agentos.core.workflow.progress import ProgressAssembler
from agentos.core.workflow.registry import WorkflowRegistry


class _VerificationAgent(BaseAgent):
    def __init__(self, status: str, calls: list[str]):
        super().__init__(
            AgentProfile(
                agentName="verification_fixture",
                domain="general",
                capabilities=["verification", "analysis"],
            )
        )
        self.status = status
        self.calls = calls

    async def run(self, context):
        capability = str(context.step.capability)
        self.calls.append(capability)
        if capability == "verification":
            return AgentOutput(
                output={
                    "verification": {
                        "status": self.status,
                        "checks": [],
                        "unresolved_gaps": ["missing acceptance evidence"],
                    }
                }
            )
        return AgentOutput(
            output={
                "analysis": {
                    "findings": ["Add acceptance evidence"],
                    "assumptions": [],
                    "gaps": [],
                }
            }
        )


class _ArtifactAgent(BaseAgent):
    def __init__(self, calls: list[str]):
        super().__init__(
            AgentProfile(
                agentName="artifact_fixture",
                domain="general",
                capabilities=["artifact_generation"],
            )
        )
        self.calls = calls

    async def run(self, context):
        self.calls.append("artifact_generation")
        return AgentOutput(output={"final_answer": "complete"})


@pytest.mark.parametrize(
    ("status", "remediation_status", "expected_calls"),
    [
        ("partial", "completed", ["verification", "analysis", "artifact_generation"]),
        ("passed", "skipped_by_condition", ["verification", "artifact_generation"]),
    ],
)
def test_native_verification_condition_routes_remediation(
    status, remediation_status, expected_calls
):
    calls: list[str] = []
    agents = AgentRegistry()
    agents.register(_VerificationAgent(status, calls))
    agents.register(_ArtifactAgent(calls))
    network = CollaborationNetwork(
        bindings=[
            CapabilityBinding(
                capability="verification",
                agent_name="verification_fixture",
                score=1,
            ),
            CapabilityBinding(
                capability="artifact_generation",
                agent_name="artifact_fixture",
                score=1,
            ),
        ]
    )
    blueprint = ACGBuilder().build(
        task_id="native_conditional",
        profile=TaskSemanticProfile(
            primaryGoal="Deliver a verified result",
            requiredCapabilities=["verification", "artifact_generation"],
        ),
        network=network,
    )
    artifact = next(
        step for step in blueprint.step_nodes() if step.capability == "artifact_generation"
    )
    artifact.output_spec = {}
    artifact.input_spec = {
        "from": dict(artifact.input_spec.get("from") or {}),
        "schema": {},
    }
    route = next(
        node
        for node in blueprint.nodes
        if isinstance(node, ControlNode) and node.control_type == ControlType.IF
    )
    assert route.node_id == "route_verification_remediation"

    workflow = WorkflowDefinition(
        workflowId="native_conditional_test",
        name="Native conditional",
        domain="general",
        intent="general",
        runtimeEngine="acg",
        steps=[
            WorkflowStepDefinition(
                stepId=step.node_id,
                name=step.name,
                agentName=step.agent_name,
                capability=step.capability,
                outputSpec=step.output_spec,
            )
            for step in blueprint.step_nodes()
        ],
    )
    workflows = WorkflowRegistry()
    workflows.register(workflow)
    runtime = WorkflowRuntime(agent_registry=agents, workflow_registry=workflows)

    async def execute():
        task = runtime.create_task(
            title="Verified result",
            domain="general",
            intent="general",
            input={"acgBlueprint": blueprint.model_dump(by_alias=True, mode="json")},
        )
        _, prepared = runtime.prepare_run(
            task.task_id,
            workflow_id=workflow.workflow_id,
            review_mode="auto",
        )
        assert "artifact_fixture" in prepared.execution_scope.agent_ids
        assert agents.resolve(
            "general",
            agent_name="artifact_fixture",
            capability="artifact_generation",
            allowed_agent_ids=prepared.execution_scope.agent_ids,
        )
        return await runtime.execute_prepared_run(prepared.run_id)

    run = asyncio.run(execute())
    graph = run.runtime_graph
    assert run.status == WorkflowStatus.COMPLETED, (
        run.error,
        calls,
        [
            (
                node.node_id,
                node.status.value,
                node.error,
                [attempt.error for attempt in node.attempts],
                node.current_binding,
            )
            for node in graph.nodes
            if node.status.value == "failed"
        ],
    )
    assert graph.graph_version == 2
    assert graph.get_node("conditional_remediation_analysis").status.value == remediation_status
    assert calls == expected_calls
    progress = ProgressAssembler().assemble(run)
    assert progress.conditional_decision_count == 1
