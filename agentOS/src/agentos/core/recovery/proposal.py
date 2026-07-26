"""Deterministic graph change proposals and bounded patch compilation."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from agentos.core.acg.edges import ACGEdge
from agentos.core.acg.enums import EdgeType
from agentos.core.acg.nodes import StepNode
from agentos.core.models.types import utc_now
from agentos.core.recovery.events import RuntimeEvent, stable_hash
from agentos.core.recovery.models import RuntimeGraphPatch, SubgraphInsertionMode
from agentos.core.recovery.policy import EventPolicyAction, EventPolicyDecision
from agentos.core.recovery.recipes import RecoveryRecipeRegistry
from agentos.core.runtime_graph import RuntimeGraph


class GraphChangeType(str, Enum):
    ADD_SUBGRAPH = "ADD_SUBGRAPH"


class CandidateBinding(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    capability: str
    agent_name: str = Field(alias="agentName")
    binding_id: str = Field(alias="bindingId")


class CandidateResolver:
    """Minimal in-memory capability resolver backed by the existing AgentRegistry."""

    def __init__(self, agent_registry) -> None:
        self.agent_registry = agent_registry

    def resolve(self, *, domain: str, capability: str) -> CandidateBinding:
        agent = self.agent_registry.resolve(domain=domain, capability=capability)
        return CandidateBinding(
            capability=capability,
            agentName=agent.profile.agent_name,
            bindingId=f"agent::{domain}::{agent.profile.agent_name}",
        )


class GraphChangeProposal(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    proposal_id: str = Field(alias="proposalId")
    idempotency_key: str = Field(alias="idempotencyKey")
    run_id: str = Field(alias="runId")
    graph_id: str = Field(alias="graphId")
    base_graph_version: int = Field(alias="baseGraphVersion", ge=1)
    source_event_id: str = Field(alias="sourceEventId")
    change_type: GraphChangeType = Field(alias="changeType")
    insertion_mode: SubgraphInsertionMode = Field(
        default=SubgraphInsertionMode.INSERT_BEFORE_TARGET,
        alias="insertionMode",
    )
    recipe_id: str = Field(alias="recipeId")
    recipe_version: str = Field(alias="recipeVersion")
    target_node_id: str = Field(alias="targetNodeId")
    reason: str
    required_capabilities: list[str] = Field(alias="requiredCapabilities")
    proposed_nodes: list[StepNode] = Field(alias="proposedNodes")
    proposed_edges: list[ACGEdge] = Field(alias="proposedEdges")
    input_mappings: dict[str, Any] = Field(default_factory=dict, alias="inputMappings")
    output_mappings: dict[str, Any] = Field(default_factory=dict, alias="outputMappings")
    created_at: datetime = Field(default_factory=utc_now, alias="createdAt")


class DeterministicProposalFactory:
    """Resolve a registered recipe into stable nodes and edges without modifying a graph."""

    def propose(
        self,
        event: RuntimeEvent,
        decision: EventPolicyDecision,
        graph: RuntimeGraph,
        recipe_registry: RecoveryRecipeRegistry,
        candidate_resolver: CandidateResolver,
        *,
        domain: str,
    ) -> GraphChangeProposal:
        if decision.action != EventPolicyAction.PROPOSE_PATCH or not decision.recipe_id:
            raise ValueError("policy decision does not authorize a graph proposal")
        recipe = recipe_registry.get(decision.recipe_id, decision.recipe_version)
        scope = stable_hash(graph.run_id, recipe.recipe_id, decision.target_node_id)
        proposal_key = stable_hash(event.event_id, recipe.recipe_id, recipe.version, decision.target_node_id)
        nodes: list[StepNode] = []
        for template in recipe.node_templates:
            binding = candidate_resolver.resolve(domain=domain, capability=template.capability)
            node_key = stable_hash(scope, template.logical_name)
            nodes.append(
                StepNode(
                    nodeId=f"runtime_{node_key[:16]}",
                    name=template.name,
                    goal=f"Apply recovery capability {template.capability}",
                    inputSpec=dict(template.input_spec),
                    outputSpec=dict(template.output_spec),
                    agentName=binding.agent_name,
                    capability=template.capability,
                    retryLimit=template.retry_limit,
                    timeout=template.timeout,
                    priority=template.priority,
                    metadata={
                        "logicalName": template.logical_name,
                        "recipeId": recipe.recipe_id,
                        "recipeVersion": recipe.version,
                        "bindingId": binding.binding_id,
                    },
                )
            )
        edges: list[ACGEdge] = []
        for source, target in zip(nodes, nodes[1:]):
            edge_key = stable_hash(scope, source.node_id, target.node_id)
            edges.append(
                ACGEdge(
                    edgeId=f"runtime_edge_{edge_key[:16]}",
                    sourceId=source.node_id,
                    targetId=target.node_id,
                    edgeType=EdgeType.DEPENDENCY,
                )
            )
        final_key = stable_hash(scope, nodes[-1].node_id, decision.target_node_id)
        edges.append(
            ACGEdge(
                edgeId=f"runtime_edge_{final_key[:16]}",
                sourceId=nodes[-1].node_id,
                targetId=decision.target_node_id,
                edgeType=EdgeType.DEPENDENCY,
            )
        )
        return GraphChangeProposal(
            proposalId=f"proposal_{proposal_key[:24]}",
            idempotencyKey=proposal_key,
            runId=graph.run_id,
            graphId=graph.graph_id,
            baseGraphVersion=graph.graph_version,
            sourceEventId=event.event_id,
            changeType=GraphChangeType.ADD_SUBGRAPH,
            insertionMode=SubgraphInsertionMode.INSERT_BEFORE_TARGET,
            recipeId=recipe.recipe_id,
            recipeVersion=recipe.version,
            targetNodeId=decision.target_node_id,
            reason=decision.reason,
            requiredCapabilities=list(recipe.required_capabilities),
            proposedNodes=nodes,
            proposedEdges=edges,
            inputMappings=dict(recipe.input_mappings),
            outputMappings=dict(recipe.output_mappings),
            createdAt=event.created_at,
        )


class RuntimeGraphPatchCompiler:
    """Compile only ADD_SUBGRAPH/INSERT_BEFORE_TARGET against the latest graph view."""

    def compile(self, proposal: GraphChangeProposal, graph: RuntimeGraph) -> RuntimeGraphPatch:
        if proposal.change_type != GraphChangeType.ADD_SUBGRAPH:
            raise ValueError(f"unsupported change type: {proposal.change_type}")
        if proposal.insertion_mode != SubgraphInsertionMode.INSERT_BEFORE_TARGET:
            raise ValueError(f"unsupported insertion mode: {proposal.insertion_mode}")
        if proposal.base_graph_version != graph.graph_version:
            raise ValueError("proposal baseGraphVersion is stale")
        incoming = [
            edge
            for edge in graph.effective_edges(EdgeType.DEPENDENCY)
            if edge.target_id == proposal.target_node_id
        ]
        first_node_id = proposal.proposed_nodes[0].node_id
        predecessor_edges = []
        for edge in incoming:
            edge_key = stable_hash(proposal.recipe_id, proposal.target_node_id, edge.source_id, first_node_id)
            predecessor_edges.append(
                ACGEdge(
                    edgeId=f"runtime_edge_{edge_key[:16]}",
                    sourceId=edge.source_id,
                    targetId=first_node_id,
                    edgeType=EdgeType.DEPENDENCY,
                )
            )
        patch_key = stable_hash(proposal.proposal_id, proposal.recipe_id, proposal.target_node_id)
        target = graph.get_node(proposal.target_node_id)
        return RuntimeGraphPatch(
            patchId=f"patch_{patch_key[:24]}",
            idempotencyKey=proposal.idempotency_key,
            runId=proposal.run_id,
            graphId=proposal.graph_id,
            baseGraphVersion=graph.graph_version,
            operationType=GraphChangeType.ADD_SUBGRAPH.value,
            sourceEventId=proposal.source_event_id,
            proposalId=proposal.proposal_id,
            reason=proposal.reason,
            createdAt=proposal.created_at,
            expectedNodeStates={proposal.target_node_id: target.status},
            budgetImpact={"addedNodes": len(proposal.proposed_nodes), "replanDepthIncrement": 1},
            metadata={
                "recipeId": proposal.recipe_id,
                "recipeVersion": proposal.recipe_version,
                "inputMappings": proposal.input_mappings,
                "outputMappings": proposal.output_mappings,
            },
            insertionMode="INSERT_BEFORE_TARGET",
            targetNodeId=proposal.target_node_id,
            replacedIncomingEdgeIds=[edge.edge_id for edge in incoming],
            addNodes=[node.model_copy(deep=True) for node in proposal.proposed_nodes],
            addEdges=[*predecessor_edges, *[edge.model_copy(deep=True) for edge in proposal.proposed_edges]],
        )


__all__ = [
    "CandidateBinding",
    "CandidateResolver",
    "DeterministicProposalFactory",
    "GraphChangeProposal",
    "GraphChangeType",
    "RuntimeGraphPatchCompiler",
]
