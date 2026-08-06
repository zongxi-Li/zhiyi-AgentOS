from __future__ import annotations

import asyncio

import pytest

from agentos.agents import AgentOutput, AgentProfile, AgentRegistry, BaseAgent
from agentos.adapters.model_adapter import StructuredGenerationError
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


class _WrappedInvalidOutputAgent(_InvalidOutputAgent):
    async def run(self, context):
        self.calls += 1
        raise StructuredGenerationError(
            "OUTPUT_CONTRACT_VIOLATION",
            "output contract violation at target: report is required",
            direction="output",
            partial_data={"partial": "unvalidated model draft"},
            model_invocations=[
                {
                    "provider": "test-provider",
                    "model": "test-model",
                    "latencyMs": 12,
                    "promptVersion": "native-capability.v1.repair1",
                    "usage": {},
                }
            ],
        )


class _EnvelopeOutputAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            AgentProfile(
                agentName="general_envelope_output",
                domain="general",
                capabilities=["produce_items"],
            )
        )
        self.calls = 0

    async def run(self, context):
        self.calls += 1
        return AgentOutput(output={"id": "item-1", "name": "Known item"})


@pytest.mark.parametrize("domain", ["legal", "general"])
def test_contract_violation_inserts_adapter_but_never_invents_report(domain):
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
    assert run.status == WorkflowStatus.FAILED
    assert graph is not None
    assert graph.graph_version == 2
    assert len(graph.applied_patch_ids) == 1
    assert len([node for node in graph.nodes if node.created_graph_version == 2]) == 1
    assert len(graph.get_node("target").attempts) == 2
    assert "report" not in graph.get_node("target").output
    assert target.calls == 2
    adapter = next(node for node in graph.nodes if node.created_graph_version == 2)
    assert adapter.output["adapter_status"] == "regeneration_required"
    assert "adapted_payload" not in adapter.output
    progress = ProgressAssembler().assemble(run)
    assert progress.dynamic_step_count == 1


def test_wrapped_output_contract_error_preserves_partial_data_without_fabrication():
    agents = AgentRegistry()
    target = _WrappedInvalidOutputAgent("general")
    agents.register(target)
    agents.register(NativeGeneralAgent())
    workflows = WorkflowRegistry()
    output_spec = {
        "type": "object",
        "properties": {"report": {"type": "string", "minLength": 1}},
        "required": ["report"],
    }
    workflow = WorkflowDefinition(
        workflowId="wrapped_contract_repair_test",
        name="Wrapped contract repair",
        domain="general",
        intent="report",
        runtimeEngine="acg",
        steps=[
            WorkflowStepDefinition(
                stepId="target",
                name="Target",
                agentName=target.profile.agent_name,
                capability="produce_report",
                outputSpec=output_spec,
            )
        ],
    )
    workflows.register(workflow)
    runtime = WorkflowRuntime(agent_registry=agents, workflow_registry=workflows)
    blueprint = ACGBlueprint(
        graphId="wrapped_contract_repair_graph",
        nodes=[
            StepNode(
                nodeId="target",
                name="Target",
                agentName=target.profile.agent_name,
                capability="produce_report",
                outputSpec=output_spec,
            )
        ],
        edges=[],
    )

    async def execute():
        task = runtime.create_task(
            title="Generate a report",
            domain="general",
            intent="report",
            input={"acgBlueprint": blueprint.model_dump(by_alias=True, mode="json")},
        )
        return await runtime.start(task.task_id, workflow_id=workflow.workflow_id)

    run = asyncio.run(execute())
    graph = run.runtime_graph
    assert run.status == WorkflowStatus.FAILED
    assert graph is not None
    assert graph.graph_version == 2
    target_node = graph.get_node("target")
    assert target_node.attempts[0].output == {"partial": "unvalidated model draft"}
    assert target_node.attempts[0].trace_context["modelInvocations"][0]["model"] == "test-model"
    assert target_node.output == {}
    assert target.calls == 2
    adapter = next(node for node in graph.nodes if node.created_graph_version == 2)
    assert adapter.output["adapter_status"] == "regeneration_required"
    assert adapter.output["adapter_source_attempt_id"] == target_node.attempts[0].attempt_id


def test_lossless_array_envelope_repair_is_validated_and_reused():
    agents = AgentRegistry()
    target = _EnvelopeOutputAgent()
    agents.register(target)
    agents.register(NativeGeneralAgent())
    workflows = WorkflowRegistry()
    output_spec = {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                    },
                    "required": ["id", "name"],
                },
            }
        },
        "required": ["items"],
    }
    workflow = WorkflowDefinition(
        workflowId="lossless_contract_repair_test",
        name="Lossless contract repair",
        domain="general",
        intent="items",
        runtimeEngine="acg",
        steps=[
            WorkflowStepDefinition(
                stepId="target",
                name="Target",
                agentName=target.profile.agent_name,
                capability="produce_items",
                outputSpec=output_spec,
            )
        ],
    )
    workflows.register(workflow)
    runtime = WorkflowRuntime(agent_registry=agents, workflow_registry=workflows)
    blueprint = ACGBlueprint(
        graphId="lossless_contract_repair_graph",
        nodes=[
            StepNode(
                nodeId="target",
                name="Target",
                agentName=target.profile.agent_name,
                capability="produce_items",
                outputSpec=output_spec,
            )
        ],
        edges=[],
    )

    async def execute():
        task = runtime.create_task(
            title="Produce items",
            domain="general",
            intent="items",
            input={"acgBlueprint": blueprint.model_dump(by_alias=True, mode="json")},
        )
        return await runtime.start(task.task_id, workflow_id=workflow.workflow_id)

    run = asyncio.run(execute())
    graph = run.runtime_graph

    assert run.status == WorkflowStatus.COMPLETED
    assert graph is not None
    assert graph.get_node("target").output == {
        "items": [{"id": "item-1", "name": "Known item"}]
    }
    assert target.calls == 1
    adapter = next(node for node in graph.nodes if node.created_graph_version == 2)
    assert adapter.output["adapter_status"] == "validated_lossless"
    assert adapter.output["repair_kind"] == "shape_only"
