"""Versioned runtime graph models derived from immutable ACG blueprints.

Stage one makes this graph authoritative for runtime *structure*, graph
versions, and patch history.  ``WorkflowStep`` remains the execution-state
authority until the executor migration in a later stage.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from agentos.core.acg.blueprint import ACGBlueprint
from agentos.core.acg.edges import ACGEdge
from agentos.core.acg.enums import EdgeType, NodeType
from agentos.core.acg.nodes import AgentNode, StepNode, parse_node


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _canonical_hash(payload: Any) -> str:
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class RuntimeNodeStatus(str, Enum):
    """Persisted runtime-node status vocabulary for the migration period."""

    PENDING = "pending"
    RUNNING = "running"
    WAITING_REVIEW = "waiting_review"
    RETRYING = "retrying"
    FAILED = "failed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class RuntimeNodeActivation(str, Enum):
    """Activation state reserved for later conditional-branch support."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    TERMINATED = "terminated"


class RuntimePatchBudget(BaseModel):
    """Testable safety limits for controlled local replanning."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    max_graph_patches: int = Field(default=3, alias="maxGraphPatches", ge=0)
    max_added_nodes_per_patch: int = Field(
        default=4, alias="maxAddedNodesPerPatch", ge=0
    )
    max_total_runtime_nodes: int = Field(default=20, alias="maxTotalRuntimeNodes", ge=1)
    max_replan_depth: int = Field(default=2, alias="maxReplanDepth", ge=0)
    current_replan_depth: int = Field(default=0, alias="currentReplanDepth", ge=0)


class RuntimeNode(BaseModel):
    """Runtime copy of one ACG node plus migration-safe execution metadata."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    node_id: str = Field(alias="nodeId")
    node_type: NodeType = Field(alias="nodeType")
    spec: dict[str, Any] = Field(default_factory=dict)
    status: RuntimeNodeStatus = RuntimeNodeStatus.PENDING
    activation: RuntimeNodeActivation = RuntimeNodeActivation.ACTIVE
    current_binding: dict[str, Any] | None = Field(default=None, alias="currentBinding")
    binding_candidates: list[dict[str, Any]] = Field(
        default_factory=list, alias="bindingCandidates"
    )
    attempts: list[dict[str, Any]] = Field(default_factory=list)
    output: dict[str, Any] = Field(default_factory=dict)
    output_version: int = Field(default=0, alias="outputVersion", ge=0)
    source_patch_id: str | None = Field(default=None, alias="sourcePatchId")
    created_graph_version: int = Field(default=1, alias="createdGraphVersion", ge=1)
    updated_at: datetime = Field(default_factory=_utc_now, alias="updatedAt")

    @classmethod
    def from_acg_node(
        cls,
        node,
        *,
        graph_version: int,
        source_patch_id: str | None = None,
    ) -> "RuntimeNode":
        """Deep-copy an ACG node without mutating the source blueprint."""

        spec = node.model_dump(by_alias=True, mode="json")
        binding: dict[str, Any] | None = None
        if isinstance(node, StepNode):
            binding = {
                "assignedAgentId": node.assigned_agent_id,
                "agentName": node.agent_name,
                "capability": node.capability,
                "skillIds": list(node.skill_ids),
            }
        return cls(
            nodeId=node.node_id,
            nodeType=node.node_type,
            spec=spec,
            currentBinding=binding,
            sourcePatchId=source_patch_id,
            createdGraphVersion=graph_version,
        )


class AppliedPatchRecord(BaseModel):
    """Immutable audit record used for replay and content-conflict checks."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    patch_id: str = Field(alias="patchId")
    idempotency_key: str = Field(alias="idempotencyKey")
    content_hash: str = Field(alias="contentHash")
    semantic_hash: str = Field(alias="semanticHash")
    operation_type: str = Field(alias="operationType")
    base_graph_version: int = Field(alias="baseGraphVersion")
    result_graph_version: int = Field(alias="resultGraphVersion")
    source_event_id: str = Field(alias="sourceEventId")
    checkpoint_id: str | None = Field(default=None, alias="checkpointId")
    applied_at: datetime = Field(default_factory=_utc_now, alias="appliedAt")


class RuntimeGraph(BaseModel):
    """Authoritative runtime structure and patch history for one workflow run."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    run_id: str = Field(alias="runId")
    graph_id: str = Field(alias="graphId")
    source_blueprint_version: int = Field(alias="sourceBlueprintVersion", ge=1)
    graph_version: int = Field(default=1, alias="graphVersion", ge=1)
    nodes: list[RuntimeNode] = Field(default_factory=list)
    edges: list[ACGEdge] = Field(default_factory=list)
    processed_event_ids: list[str] = Field(
        default_factory=list, alias="processedEventIds"
    )
    applied_patch_ids: list[str] = Field(default_factory=list, alias="appliedPatchIds")
    applied_patch_idempotency_keys: list[str] = Field(
        default_factory=list,
        alias="appliedPatchIdempotencyKeys",
    )
    applied_patches: list[AppliedPatchRecord] = Field(
        default_factory=list, alias="appliedPatches"
    )
    patch_budget: RuntimePatchBudget = Field(
        default_factory=RuntimePatchBudget, alias="patchBudget"
    )
    created_at: datetime = Field(default_factory=_utc_now, alias="createdAt")
    updated_at: datetime = Field(default_factory=_utc_now, alias="updatedAt")

    @classmethod
    def from_blueprint(
        cls,
        *,
        run_id: str,
        blueprint: ACGBlueprint,
        agent_registry: Any | None = None,
        domain: str = "",
    ) -> "RuntimeGraph":
        """Create deterministic runtime structure from a deep blueprint copy."""

        graph = cls(
            runId=run_id,
            graphId=blueprint.graph_id,
            sourceBlueprintVersion=blueprint.version,
            graphVersion=1,
            nodes=[
                RuntimeNode.from_acg_node(node, graph_version=1)
                for node in blueprint.nodes
            ],
            edges=[edge.model_copy(deep=True) for edge in blueprint.edges],
        )
        graph.enrich_bindings(agent_registry=agent_registry, domain=domain)
        return graph

    def get_node(self, node_id: str) -> RuntimeNode:
        for node in self.nodes:
            if node.node_id == node_id:
                return node
        raise KeyError(f"runtime node not found: {node_id}")

    def has_node(self, node_id: str) -> bool:
        return any(node.node_id == node_id for node in self.nodes)

    def effective_edges(self, edge_type: EdgeType | None = None) -> list[ACGEdge]:
        """Return edges not superseded by an applied runtime patch."""

        return [
            edge
            for edge in self.edges
            if not edge.metadata.get("supersededByPatchId")
            and (edge_type is None or edge.edge_type == edge_type)
        ]

    def to_blueprint(self, *, effective_only: bool = True) -> ACGBlueprint:
        """Build a validation view without changing this RuntimeGraph."""

        edges = self.effective_edges() if effective_only else list(self.edges)
        return ACGBlueprint(
            graphId=self.graph_id,
            version=self.source_blueprint_version,
            nodes=[parse_node(node.spec) for node in self.nodes],
            edges=[edge.model_copy(deep=True) for edge in edges],
            metadata={"runtimeGraphVersion": self.graph_version},
        )

    def patch_record_by_id(self, patch_id: str) -> AppliedPatchRecord | None:
        return next(
            (item for item in self.applied_patches if item.patch_id == patch_id), None
        )

    def patch_record_by_idempotency_key(self, key: str) -> AppliedPatchRecord | None:
        return next(
            (item for item in self.applied_patches if item.idempotency_key == key), None
        )

    def enrich_bindings(self, *, agent_registry: Any | None, domain: str) -> None:
        """Enrich runtime bindings while leaving the design blueprint untouched."""

        agent_nodes = {
            node.node_id: node
            for node in (parse_node(item.spec) for item in self.nodes)
            if isinstance(node, AgentNode)
        }
        for runtime_node in self.nodes:
            acg_node = parse_node(runtime_node.spec)
            if not isinstance(acg_node, StepNode):
                continue
            execution_edges = [
                edge
                for edge in self.effective_edges(EdgeType.EXECUTION)
                if edge.target_id == runtime_node.node_id
            ]
            assigned_id = acg_node.assigned_agent_id or (
                execution_edges[0].source_id if execution_edges else None
            )
            binding = dict(runtime_node.current_binding or {})
            binding["assignedAgentId"] = assigned_id
            if assigned_id and assigned_id in agent_nodes:
                binding["modelName"] = agent_nodes[assigned_id].model_name
            if agent_registry is not None:
                agent = agent_registry.resolve(
                    domain=domain,
                    agent_name=acg_node.agent_name,
                    capability=acg_node.capability,
                )
                binding["allowedSkills"] = list(
                    dict.fromkeys(agent.profile.allowed_skills)
                )
            runtime_node.current_binding = binding

    def structure_hash(self) -> str:
        """Hash graph structure and patch lineage, excluding mutable node state."""

        return _canonical_hash(
            {
                "graphId": self.graph_id,
                "graphVersion": self.graph_version,
                "nodes": [node.spec for node in self.nodes],
                "edges": [
                    edge.model_dump(by_alias=True, mode="json") for edge in self.edges
                ],
                "appliedPatchIds": self.applied_patch_ids,
            }
        )


__all__ = [
    "AppliedPatchRecord",
    "RuntimeGraph",
    "RuntimeNode",
    "RuntimeNodeActivation",
    "RuntimeNodeStatus",
    "RuntimePatchBudget",
]
