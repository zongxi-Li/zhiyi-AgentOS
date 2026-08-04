from __future__ import annotations

import asyncio

import pytest

from agentos.agents import AgentRegistry
from agentos.agents.registry import AgentNotFound
from agentos.core.acg import ACGBlueprint, StepNode
from agentos.core.models.types import WorkflowDefinition, WorkflowStatus, WorkflowStepDefinition
from agentos.core.native import NativeGeneralAgent, NativeGeneralFallbackAgent
from agentos.core.runtime import WorkflowRuntime
from agentos.core.workflow.registry import WorkflowRegistry
from packs.legal.agents.contract_review_migration import LegalEvidenceMatchAgent
from packs.legal.agents.fallback import LegalWorkflowFallbackAgent
from packs.legal.planning.capabilities import LEGAL_CAPABILITY_RUNTIME_IDS


@pytest.mark.parametrize(
    ("stable_id", "runtime_id"),
    LEGAL_CAPABILITY_RUNTIME_IDS.items(),
)
def test_legal_fallback_accepts_planner_capability_ids(stable_id, runtime_id):
    fallback = LegalWorkflowFallbackAgent()

    assert stable_id in fallback.profile.capabilities
    assert fallback._delegates[stable_id] is fallback._delegates[runtime_id]


@pytest.mark.parametrize(
    ("domain", "capability", "primary", "fallback"),
    [
        (
            "general",
            "contract_adapter",
            NativeGeneralAgent,
            NativeGeneralFallbackAgent,
        ),
        (
            "legal",
            "legal_evidence_match",
            LegalEvidenceMatchAgent,
            LegalWorkflowFallbackAgent,
        ),
    ],
)
def test_pack_primary_failure_switches_to_registered_fallback(
    domain, capability, primary, fallback
):
    primary_agent = primary()
    fallback_agent = fallback()

    async def unavailable(context):
        raise AgentNotFound("primary binding disappeared")

    primary_agent.run = unavailable
    agents = AgentRegistry()
    agents.register(primary_agent)
    agents.register(fallback_agent)
    workflow = WorkflowDefinition(
        workflowId=f"{domain}_pack_binding_test",
        name="Pack binding",
        domain=domain,
        intent="test",
        runtimeEngine="acg",
        steps=[
            WorkflowStepDefinition(
                stepId="target",
                name="Target",
                agentName=primary_agent.profile.agent_name,
                capability=capability,
                maxRetries=1,
            )
        ],
    )
    workflows = WorkflowRegistry()
    workflows.register(workflow)
    runtime = WorkflowRuntime(agent_registry=agents, workflow_registry=workflows)
    blueprint = ACGBlueprint(
        graphId=f"{domain}_pack_binding_graph",
        nodes=[
            StepNode(
                nodeId="target",
                name="Target",
                agentName=primary_agent.profile.agent_name,
                capability=capability,
                retryLimit=1,
            )
        ],
        edges=[],
    )

    async def execute():
        task = runtime.create_task(
            title="Binding recovery",
            domain=domain,
            intent="test",
            input={"acgBlueprint": blueprint.model_dump(by_alias=True, mode="json")},
        )
        return await runtime.start(task.task_id, workflow_id=workflow.workflow_id)

    run = asyncio.run(execute())
    node = run.runtime_graph.get_node("target")
    assert run.status == WorkflowStatus.COMPLETED
    assert run.runtime_graph.graph_version == 2
    assert node.binding_switch_count == 1
    assert [attempt.agent_name for attempt in node.attempts] == [
        primary_agent.profile.agent_name,
        fallback_agent.profile.agent_name,
    ]
