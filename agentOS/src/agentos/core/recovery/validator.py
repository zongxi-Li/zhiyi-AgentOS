"""Pure validation and candidate construction for bounded runtime patches."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping

from agentos.core.acg.enums import EdgeType, NodeType
from agentos.core.acg.graph_ops import ACGValidationError, validate_blueprint
from agentos.core.acg.nodes import StepNode
from agentos.core.recovery.errors import PatchValidationError
from agentos.core.recovery.models import (
    PatchOperationType,
    RuntimeGraphPatch,
    SubgraphInsertionMode,
)
from agentos.core.runtime_graph import RuntimeGraph, RuntimeNode, RuntimeNodeStatus


_IMMUTABLE_TARGET_STATES = {
    RuntimeNodeStatus.COMPLETED,
    RuntimeNodeStatus.CANCELLED,
}


class PatchValidator:
    """Validate a patch against a graph copy; never mutate caller-owned objects."""

    def __init__(self, agent_registry) -> None:
        self.agent_registry = agent_registry

    def validate(
        self,
        graph: RuntimeGraph,
        patch: RuntimeGraphPatch,
        *,
        domain: str,
        authoritative_step_states: Mapping[str, str] | None = None,
    ) -> RuntimeGraph:
        """Return a validated candidate graph without advancing its version."""

        self._validate_identity(graph, patch)
        self._validate_budget(graph, patch)
        self._validate_target_and_replaced_edges(
            graph,
            patch,
            authoritative_step_states=authoritative_step_states,
        )
        self._validate_ids(graph, patch)
        self._validate_capabilities(patch, domain=domain)

        candidate = graph.model_copy(deep=True)
        next_version = graph.graph_version + 1
        for edge in candidate.edges:
            if edge.edge_id in patch.replaced_incoming_edge_ids:
                edge.metadata["supersededByPatchId"] = patch.patch_id
                edge.metadata["supersededAtGraphVersion"] = next_version
        candidate.nodes.extend(
            RuntimeNode.from_acg_node(
                node.model_copy(deep=True),
                graph_version=next_version,
                source_patch_id=patch.patch_id,
            )
            for node in patch.add_nodes
        )
        for edge in patch.add_edges:
            copied = edge.model_copy(deep=True)
            copied.metadata["sourcePatchId"] = patch.patch_id
            copied.metadata["createdGraphVersion"] = next_version
            candidate.edges.append(copied)

        self._validate_insertion_connectivity(graph, candidate, patch)
        try:
            validate_blueprint(candidate.to_blueprint(effective_only=True))
        except (ACGValidationError, ValueError, TypeError) as exc:
            raise PatchValidationError("INVALID_RUNTIME_GRAPH", str(exc)) from exc
        candidate.enrich_bindings(agent_registry=self.agent_registry, domain=domain)
        candidate.patch_budget.current_replan_depth += (
            patch.budget_impact.replan_depth_increment
        )
        return candidate

    @staticmethod
    def _validate_identity(graph: RuntimeGraph, patch: RuntimeGraphPatch) -> None:
        if patch.run_id != graph.run_id:
            raise PatchValidationError(
                "RUN_ID_MISMATCH", "patch runId does not match RuntimeGraph"
            )
        if patch.graph_id != graph.graph_id:
            raise PatchValidationError(
                "GRAPH_ID_MISMATCH", "patch graphId does not match RuntimeGraph"
            )
        if patch.base_graph_version != graph.graph_version:
            raise PatchValidationError(
                "GRAPH_VERSION_CONFLICT",
                f"expected graphVersion {graph.graph_version}, got {patch.base_graph_version}",
            )
        if patch.operation_type != PatchOperationType.ADD_SUBGRAPH:
            raise PatchValidationError(
                "UNSUPPORTED_PATCH_OPERATION", str(patch.operation_type)
            )
        if patch.insertion_mode != SubgraphInsertionMode.INSERT_BEFORE_TARGET:
            raise PatchValidationError(
                "UNSUPPORTED_INSERTION_MODE", str(patch.insertion_mode)
            )
        if not patch.patch_id.strip() or not patch.idempotency_key.strip():
            raise PatchValidationError(
                "INVALID_PATCH_IDENTITY", "patchId and idempotencyKey are required"
            )

    @staticmethod
    def _validate_budget(graph: RuntimeGraph, patch: RuntimeGraphPatch) -> None:
        budget = graph.patch_budget
        if len(graph.applied_patch_ids) >= budget.max_graph_patches:
            raise PatchValidationError(
                "PATCH_BUDGET_EXCEEDED", "maximum graph patch count reached"
            )
        if len(patch.add_nodes) > budget.max_added_nodes_per_patch:
            raise PatchValidationError(
                "ADDED_NODE_BUDGET_EXCEEDED", "too many nodes in one patch"
            )
        if len(graph.nodes) + len(patch.add_nodes) > budget.max_total_runtime_nodes:
            raise PatchValidationError(
                "TOTAL_NODE_BUDGET_EXCEEDED", "runtime graph node budget exceeded"
            )
        if patch.budget_impact.added_nodes != len(patch.add_nodes):
            raise PatchValidationError(
                "BUDGET_IMPACT_MISMATCH", "budgetImpact.addedNodes is inaccurate"
            )
        depth = budget.current_replan_depth + patch.budget_impact.replan_depth_increment
        if depth > budget.max_replan_depth:
            raise PatchValidationError(
                "REPLAN_DEPTH_EXCEEDED", "maximum replan depth exceeded"
            )

    @staticmethod
    def _validate_target_and_replaced_edges(
        graph: RuntimeGraph,
        patch: RuntimeGraphPatch,
        *,
        authoritative_step_states: Mapping[str, str] | None,
    ) -> None:
        try:
            target = graph.get_node(patch.target_node_id)
        except KeyError as exc:
            raise PatchValidationError(
                "TARGET_NODE_NOT_FOUND", patch.target_node_id
            ) from exc
        if target.node_type != NodeType.STEP:
            raise PatchValidationError(
                "INVALID_TARGET_NODE", "target must be a Step node"
            )
        target_status = RuntimeNodeStatus(
            (authoritative_step_states or {}).get(target.node_id, target.status.value)
        )
        if target_status in _IMMUTABLE_TARGET_STATES:
            raise PatchValidationError(
                "TARGET_STATE_CONFLICT", f"target is {target_status.value}"
            )
        for node_id, expected in patch.expected_node_states.items():
            try:
                runtime_status = graph.get_node(node_id).status
            except KeyError as exc:
                raise PatchValidationError("EXPECTED_NODE_NOT_FOUND", node_id) from exc
            actual = RuntimeNodeStatus(
                (authoritative_step_states or {}).get(node_id, runtime_status.value)
            )
            if actual != expected:
                raise PatchValidationError(
                    "EXPECTED_NODE_STATE_CONFLICT",
                    f"{node_id}: expected {expected.value}, got {actual.value}",
                )

        if len(set(patch.replaced_incoming_edge_ids)) != len(
            patch.replaced_incoming_edge_ids
        ):
            raise PatchValidationError(
                "DUPLICATE_REPLACED_EDGE_ID", "replaced edge ids must be unique"
            )
        incoming = {
            edge.edge_id: edge
            for edge in graph.effective_edges(EdgeType.DEPENDENCY)
            if edge.target_id == patch.target_node_id
        }
        invalid = [
            edge_id
            for edge_id in patch.replaced_incoming_edge_ids
            if edge_id not in incoming
        ]
        if invalid:
            raise PatchValidationError(
                "INVALID_REPLACED_EDGE",
                f"edges are not active incoming dependencies of target: {invalid}",
            )
        if incoming and not patch.replaced_incoming_edge_ids:
            raise PatchValidationError(
                "MISSING_REPLACED_EDGE", "target has incoming dependencies"
            )

    @staticmethod
    def _validate_ids(graph: RuntimeGraph, patch: RuntimeGraphPatch) -> None:
        node_ids = [node.node_id for node in patch.add_nodes]
        edge_ids = [edge.edge_id for edge in patch.add_edges]
        if len(node_ids) != len(set(node_ids)):
            raise PatchValidationError(
                "DUPLICATE_NODE_ID", "patch contains duplicate node ids"
            )
        if len(edge_ids) != len(set(edge_ids)):
            raise PatchValidationError(
                "DUPLICATE_EDGE_ID", "patch contains duplicate edge ids"
            )
        existing_nodes = {node.node_id for node in graph.nodes}
        existing_edges = {edge.edge_id for edge in graph.edges}
        collisions = sorted(existing_nodes.intersection(node_ids))
        if collisions:
            raise PatchValidationError("NODE_ID_CONFLICT", str(collisions))
        collisions = sorted(existing_edges.intersection(edge_ids))
        if collisions:
            raise PatchValidationError("EDGE_ID_CONFLICT", str(collisions))

        all_nodes = existing_nodes.union(node_ids)
        completed_nodes = {
            node.node_id
            for node in graph.nodes
            if node.status == RuntimeNodeStatus.COMPLETED
        }
        added_nodes = set(node_ids)
        replaced_predecessors = {
            edge.source_id
            for edge in graph.effective_edges(EdgeType.DEPENDENCY)
            if edge.edge_id in patch.replaced_incoming_edge_ids
        }
        for edge in patch.add_edges:
            if edge.source_id not in all_nodes or edge.target_id not in all_nodes:
                raise PatchValidationError(
                    "EDGE_ENDPOINT_NOT_FOUND",
                    f"{edge.edge_id}: {edge.source_id} -> {edge.target_id}",
                )
            if edge.target_id in completed_nodes:
                raise PatchValidationError(
                    "COMPLETED_NODE_MODIFICATION",
                    f"new edge {edge.edge_id} targets completed node {edge.target_id}",
                )
            if edge.edge_type == EdgeType.DEPENDENCY:
                allowed_target = (
                    edge.target_id in added_nodes
                    or edge.target_id == patch.target_node_id
                )
                allowed_source = (
                    edge.source_id in added_nodes
                    or edge.source_id in replaced_predecessors
                )
                if not allowed_target or not allowed_source:
                    raise PatchValidationError(
                        "OUT_OF_SCOPE_DEPENDENCY_EDIT",
                        f"dependency {edge.edge_id} is outside INSERT_BEFORE_TARGET",
                    )
                if (
                    edge.target_id == patch.target_node_id
                    and edge.source_id not in added_nodes
                ):
                    raise PatchValidationError(
                        "TARGET_BYPASSES_SUBGRAPH",
                        f"dependency {edge.edge_id} reaches target without an added node",
                    )

    def _validate_capabilities(self, patch: RuntimeGraphPatch, *, domain: str) -> None:
        for node in patch.add_nodes:
            if not isinstance(node, StepNode):
                continue
            try:
                self.agent_registry.resolve(
                    domain=domain,
                    agent_name=node.agent_name,
                    capability=node.capability,
                )
            except KeyError as exc:
                raise PatchValidationError(
                    "UNREGISTERED_CAPABILITY",
                    f"node {node.node_id}: {node.agent_name}/{node.capability}",
                ) from exc

    @staticmethod
    def _validate_insertion_connectivity(
        original: RuntimeGraph,
        candidate: RuntimeGraph,
        patch: RuntimeGraphPatch,
    ) -> None:
        adjacency: dict[str, set[str]] = defaultdict(set)
        for edge in candidate.effective_edges(EdgeType.DEPENDENCY):
            adjacency[edge.source_id].add(edge.target_id)

        def has_path(source: str, target: str) -> bool:
            frontier = [source]
            seen: set[str] = set()
            while frontier:
                current = frontier.pop()
                if current == target:
                    return True
                if current in seen:
                    continue
                seen.add(current)
                frontier.extend(adjacency.get(current, ()))
            return False

        replaced = {
            edge.edge_id: edge
            for edge in original.effective_edges(EdgeType.DEPENDENCY)
            if edge.edge_id in patch.replaced_incoming_edge_ids
        }
        new_ids = {node.node_id for node in patch.add_nodes}
        if not any(
            edge.edge_type == EdgeType.DEPENDENCY
            and edge.source_id in new_ids
            and edge.target_id == patch.target_node_id
            for edge in patch.add_edges
        ):
            raise PatchValidationError(
                "SUBGRAPH_NOT_CONNECTED_TO_TARGET", patch.target_node_id
            )
        for predecessor in {edge.source_id for edge in replaced.values()}:
            if not any(has_path(predecessor, new_id) for new_id in new_ids):
                raise PatchValidationError("PREDECESSOR_NOT_CONNECTED", predecessor)
        for node_id in new_ids:
            if not has_path(node_id, patch.target_node_id):
                raise PatchValidationError("ADDED_NODE_NOT_CONNECTED", node_id)


__all__ = ["PatchValidator"]
