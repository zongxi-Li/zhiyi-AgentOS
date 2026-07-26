"""Typed inputs and results for controlled runtime-graph patching."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from agentos.core.acg.edges import ACGEdge
from agentos.core.acg.nodes import ACGNode, parse_node
from agentos.core.models.types import utc_now
from agentos.core.runtime_graph import RuntimeGraph, RuntimeNodeStatus


def _hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class PatchOperationType(str, Enum):
    ADD_SUBGRAPH = "ADD_SUBGRAPH"


class SubgraphInsertionMode(str, Enum):
    INSERT_BEFORE_TARGET = "INSERT_BEFORE_TARGET"


class PatchBudgetImpact(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    added_nodes: int = Field(default=0, alias="addedNodes", ge=0)
    replan_depth_increment: int = Field(default=1, alias="replanDepthIncrement", ge=0)


class RuntimeGraphPatch(BaseModel):
    """A bounded request to insert a subgraph immediately before one target."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    patch_id: str = Field(alias="patchId", min_length=1)
    idempotency_key: str = Field(alias="idempotencyKey", min_length=1)
    run_id: str = Field(alias="runId", min_length=1)
    graph_id: str = Field(alias="graphId", min_length=1)
    base_graph_version: int = Field(alias="baseGraphVersion", ge=1)
    operation_type: PatchOperationType = Field(alias="operationType")
    source_event_id: str = Field(alias="sourceEventId", min_length=1)
    proposal_id: str = Field(alias="proposalId", min_length=1)
    reason: str = ""
    created_at: datetime = Field(default_factory=utc_now, alias="createdAt")
    expected_node_states: dict[str, RuntimeNodeStatus] = Field(
        default_factory=dict,
        alias="expectedNodeStates",
    )
    budget_impact: PatchBudgetImpact = Field(alias="budgetImpact")
    metadata: dict[str, Any] = Field(default_factory=dict)
    insertion_mode: SubgraphInsertionMode = Field(
        default=SubgraphInsertionMode.INSERT_BEFORE_TARGET,
        alias="insertionMode",
    )
    target_node_id: str = Field(alias="targetNodeId", min_length=1)
    replaced_incoming_edge_ids: list[str] = Field(alias="replacedIncomingEdgeIds")
    add_nodes: list[ACGNode] = Field(alias="addNodes", min_length=1)
    add_edges: list[ACGEdge] = Field(alias="addEdges", min_length=1)

    @field_validator("add_nodes", mode="before")
    @classmethod
    def _parse_nodes(cls, value):
        return [parse_node(item) for item in value]

    def content_hash(self) -> str:
        return _hash(self.model_dump(by_alias=True, mode="json"))

    def semantic_hash(self) -> str:
        payload = self.model_dump(by_alias=True, mode="json")
        for key in (
            "patchId",
            "idempotencyKey",
            "createdAt",
            "sourceEventId",
            "proposalId",
            "reason",
        ):
            payload.pop(key, None)
        return _hash(payload)


class PatchApplyResult(BaseModel):
    """Result of applying or idempotently replaying a persisted patch."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    applied: bool
    idempotent_replay: bool = Field(default=False, alias="idempotentReplay")
    graph_version: int = Field(alias="graphVersion")
    patch_id: str = Field(alias="patchId")
    checkpoint_id: str | None = Field(default=None, alias="checkpointId")
    runtime_graph: RuntimeGraph = Field(alias="runtimeGraph")


__all__ = [
    "PatchApplyResult",
    "PatchBudgetImpact",
    "PatchOperationType",
    "RuntimeGraphPatch",
    "SubgraphInsertionMode",
]
