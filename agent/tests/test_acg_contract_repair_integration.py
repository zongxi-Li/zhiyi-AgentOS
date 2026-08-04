from __future__ import annotations

import asyncio

import pytest

from agentos.agents import AgentOutput, AgentProfile, AgentRegistry, BaseAgent
from agentos.core.acg import ACGBlueprint, StepNode
from agentos.core.models.types import WorkflowDefinition, WorkflowStatus, WorkflowStepDefinition
from agentos.core.native import NativeGeneralAgent
from agentos.core.runtime import WorkflowRuntime
from agentos.core.workflow.progress import ProgressAssembler
from agentos.core.workflow.registry import WorkflowRegistry
from packs.legal.agents.recovery import LegalContractAdapterAgent


class _InvalidOutputAgent(BaseAgent):
    def __init__(self, domain: str):
        super().__init__(
            AgentProfile(
                agentName=f"{domain}_invalid_output",
                domain=domain,
                capabilities=["produce_report"],
            )
        )
        self.calls = 0

    async def run(self, context):
        self.calls += 1
        return AgentOutput(output={"partial": "unvalidated draft"})


@pytest.mark.parametrize("domain", ["legal", "general"])
def test_contract_violation_inserts_adapter_and_reuses_repaired_output(domain):
    agents = AgentRegistry()
    target = _InvalidOutputAgent(domain)
    agents.register(target)
    if domain == "legal":
        agents.register(LegalContractAdapterAgent())
    else:
        agents.register(NativeGeneralAgent())
    workflows = WorkflowRegistry()
    workflow = WorkflowDefinition(
        workflowId=f"{domain}_contract_repair_test",
        name="Contract repair",
        domain=domain,
        intent="report",
        runtimeEngine="acg",
        steps=[
            WorkflowStepDefinition(
                stepId="target",
                name="Target",
                agentName=target.profile.agent_name,
                capability="produce_report",
                outputSpec={
                    "type": "object",
                    "properties": {"report": {"type": "string", "minLength": 1}},
                    "required": ["report"],
                },
            )
        ],
    )
    workflows.register(workflow)
    runtime = WorkflowRuntime(agent_registry=agents, workflow_registry=workflows)
    blueprint = ACGBlueprint(
        graphId=f"{domain}_contract_repair_graph",
        nodes=[
            StepNode(
                nodeId="target",
                name="Target",
                agentName=target.profile.agent_name,
                capability="produce_report",
                outputSpec=workflow.steps[0].output_spec,
            )
        ],
        edges=[],
    )

    async def execute():
        task = runtime.create_task(
            title="Generate a report",
            domain=domain,
            intent="report",
            input={"acgBlueprint": blueprint.model_dump(by_alias=True, mode="json")},
        )
        return await runtime.start(task.task_id, workflow_id=workflow.workflow_id)

    run = asyncio.run(execute())
    graph = run.runtime_graph
    assert run.status == WorkflowStatus.COMPLETED
    assert graph is not None
    assert graph.graph_version == 2
    assert len(graph.applied_patch_ids) == 1
    assert len([node for node in graph.nodes if node.created_graph_version == 2]) == 1
    assert len(graph.get_node("target").attempts) == 2
    assert graph.get_node("target").output["report"] == "unknown"
    assert target.calls == 1
    progress = ProgressAssembler().assemble(run)
    assert progress.dynamic_step_count == 1

