"""Declarative, bounded IF-route construction for ACG blueprints."""

from __future__ import annotations

from typing import Any

from agentos.core.acg.edges import ACGEdge
from agentos.core.acg.enums import ControlType, EdgeType
from agentos.core.acg.nodes import ControlNode
from agentos.core.conditions import ConditionSpec


def apply_conditional_route(blueprint, route: dict[str, Any]) -> None:
    """Insert one convergent conditional route without expression evaluation."""

    control_id = str(route["controlNodeId"])
    after_id = str(route["afterStepId"])
    source_id = str(route.get("sourceStepId") or after_id)
    join_id = str(route["joinNodeId"])
    before_id = str(route["joinBeforeStepId"])
    case_targets = {str(key): str(value) for key, value in dict(route["cases"]).items()}
    default_target = str(route.get("defaultTargetStepId") or "$join")
    branch_ends = [str(value) for value in route.get("branchEndStepIds") or []]
    concrete_targets = {
        target for target in [*case_targets.values(), default_target] if target != "$join"
    }

    blueprint.nodes.extend(
        [
            ControlNode(
                nodeId=control_id,
                name=str(route.get("name") or "Conditional route"),
                controlType=ControlType.IF,
                joinNodeId=join_id,
                metadata={"declarativeRoute": True},
            ),
            ControlNode(
                nodeId=join_id,
                name=str(route.get("joinName") or "Conditional join"),
                controlType=ControlType.CONSENSUS,
                metadata={"declarativeRoute": True},
            ),
        ]
    )

    removable_pairs = {
        (after_id, target) for target in concrete_targets | {before_id}
    } | {(end_id, before_id) for end_id in branch_ends}
    blueprint.edges = [
        edge
        for edge in blueprint.edges
        if not (
            edge.edge_type == EdgeType.DEPENDENCY
            and (edge.source_id, edge.target_id) in removable_pairs
        )
    ]
    blueprint.edges.append(
        ACGEdge(
            edgeId=f"{control_id}__after",
            sourceId=after_id,
            targetId=control_id,
            edgeType=EdgeType.DEPENDENCY,
        )
    )
    if source_id != after_id:
        raise ValueError("conditional route sourceStepId must equal afterStepId")

    edge_by_target: dict[str, str] = {}
    for index, target in enumerate(sorted(concrete_targets | ({default_target} - {"$join"})), start=1):
        edge_id = f"{control_id}__branch_{index}"
        edge_by_target[target] = edge_id
        blueprint.edges.append(
            ACGEdge(
                edgeId=edge_id,
                sourceId=control_id,
                targetId=target,
                edgeType=EdgeType.DEPENDENCY,
            )
        )
    join_edge_id = f"{control_id}__branch_join"
    if "$join" in case_targets.values() or default_target == "$join":
        edge_by_target["$join"] = join_edge_id
        blueprint.edges.append(
            ACGEdge(
                edgeId=join_edge_id,
                sourceId=control_id,
                targetId=join_id,
                edgeType=EdgeType.DEPENDENCY,
            )
        )
    for end_id in branch_ends:
        blueprint.edges.append(
            ACGEdge(
                edgeId=f"{control_id}__{end_id}_join",
                sourceId=end_id,
                targetId=join_id,
                edgeType=EdgeType.DEPENDENCY,
            )
        )
    blueprint.edges.append(
        ACGEdge(
            edgeId=f"{control_id}__join_next",
            sourceId=join_id,
            targetId=before_id,
            edgeType=EdgeType.DEPENDENCY,
        )
    )

    control = blueprint.get_node(control_id)
    control.condition_spec = ConditionSpec(
        sourceNodeId=source_id,
        jsonPointer=str(route.get("jsonPointer") or ""),
        operator=str(route.get("operator") or "EQUALS"),
        cases={key: edge_by_target[target] for key, target in case_targets.items()},
        defaultEdgeId=edge_by_target[default_target],
        valueType=str(route.get("valueType") or "string"),
    )
    control.branch_edge_ids = list(dict.fromkeys(control.condition_spec.cases.values()))
    if control.condition_spec.default_edge_id not in control.branch_edge_ids:
        control.branch_edge_ids.append(control.condition_spec.default_edge_id)


__all__ = ["apply_conditional_route"]
