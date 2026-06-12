"""ACG 图算法：环检测、拓扑排序、悬空依赖检查、就绪集计算。

这些算法服务两处：
1. 规划器在交付蓝图前做图级验证（非循环性、无悬空依赖）。
2. 执行器在运行时按 DEPENDENCY 边计算“就绪集”，驱动并行调度。

仅依赖 DEPENDENCY 边构建执行 DAG；其它边（通信、记忆读写、证据支撑）
不影响执行先后，由通信器/记忆器/审计器分别消费。
"""

from __future__ import annotations

from typing import Dict, List, Set

from agentos.core.acg.blueprint import ACGBlueprint
from agentos.core.acg.enums import EdgeType, NodeType


class ACGValidationError(ValueError):
    """ACG 图结构非法（成环或悬空依赖）。"""


def _dependency_adjacency(blueprint: ACGBlueprint) -> Dict[str, List[str]]:
    """构建仅含 STEP/CONTROL 节点的 DEPENDENCY 邻接表（source -> [targets]）。"""
    executable_ids = {
        n.node_id for n in blueprint.nodes
        if n.node_type in {NodeType.STEP, NodeType.CONTROL}
    }
    adjacency: Dict[str, List[str]] = {nid: [] for nid in executable_ids}
    for edge in blueprint.edges_of_type(EdgeType.DEPENDENCY):
        if edge.source_id in executable_ids and edge.target_id in executable_ids:
            adjacency[edge.source_id].append(edge.target_id)
    return adjacency


def detect_cycle(blueprint: ACGBlueprint) -> List[str]:
    """检测 DEPENDENCY 子图是否成环。返回构成环的节点 id 列表（无环则空）。"""
    adjacency = _dependency_adjacency(blueprint)
    WHITE, GRAY, BLACK = 0, 1, 2
    color: Dict[str, int] = {nid: WHITE for nid in adjacency}
    stack: List[str] = []

    def visit(node_id: str) -> List[str]:
        color[node_id] = GRAY
        stack.append(node_id)
        for nxt in adjacency.get(node_id, []):
            if color.get(nxt, WHITE) == GRAY:
                # 回边：截取从 nxt 到当前的栈片段作为环
                idx = stack.index(nxt)
                return stack[idx:] + [nxt]
            if color.get(nxt, WHITE) == WHITE:
                found = visit(nxt)
                if found:
                    return found
        color[node_id] = BLACK
        stack.pop()
        return []

    for nid in adjacency:
        if color[nid] == WHITE:
            cycle = visit(nid)
            if cycle:
                return cycle
    return []


def topological_order(blueprint: ACGBlueprint) -> List[str]:
    """Kahn 算法对 DEPENDENCY 子图做拓扑排序。成环则抛 ACGValidationError。"""
    adjacency = _dependency_adjacency(blueprint)
    indegree: Dict[str, int] = {nid: 0 for nid in adjacency}
    for targets in adjacency.values():
        for t in targets:
            indegree[t] = indegree.get(t, 0) + 1

    queue = [nid for nid, deg in indegree.items() if deg == 0]
    order: List[str] = []
    while queue:
        queue.sort()  # 稳定输出，便于测试
        node_id = queue.pop(0)
        order.append(node_id)
        for nxt in adjacency.get(node_id, []):
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)

    if len(order) != len(adjacency):
        raise ACGValidationError(f"ACG contains a cycle; topological sort impossible. cycle={detect_cycle(blueprint)}")
    return order


def find_dangling_dependencies(blueprint: ACGBlueprint) -> List[str]:
    """返回引用了不存在节点的 DEPENDENCY 边 id 列表。"""
    dangling: List[str] = []
    for edge in blueprint.edges_of_type(EdgeType.DEPENDENCY):
        if not blueprint.has_node(edge.source_id) or not blueprint.has_node(edge.target_id):
            dangling.append(edge.edge_id)
    return dangling


def validate_blueprint(blueprint: ACGBlueprint) -> None:
    """规划器交付前的图级验证。非法则抛 ACGValidationError。"""
    dangling = find_dangling_dependencies(blueprint)
    if dangling:
        raise ACGValidationError(f"ACG has dangling dependency edges: {dangling}")
    cycle = detect_cycle(blueprint)
    if cycle:
        raise ACGValidationError(f"ACG contains a cycle: {' -> '.join(cycle)}")


def ready_steps(blueprint: ACGBlueprint, completed: Set[str]) -> List[str]:
    """计算就绪集：所有 DEPENDENCY 前驱都已完成、且自身未完成的 STEP 节点。

    这是执行器并行调度的核心：返回的全部 step 之间彼此无依赖，可并发执行。
    """
    ready: List[str] = []
    for step in blueprint.step_nodes():
        if step.node_id in completed:
            continue
        deps = blueprint.dependency_sources(step.node_id)
        if all(dep in completed for dep in deps):
            ready.append(step.node_id)
    return ready


__all__ = [
    "ACGValidationError",
    "detect_cycle",
    "topological_order",
    "find_dangling_dependencies",
    "validate_blueprint",
    "ready_steps",
]
