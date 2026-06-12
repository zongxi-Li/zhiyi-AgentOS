"""线性工作流 → ACG 自动升格。

现有 WorkflowDefinition 是基于 nextStepId 的线性步骤链。本模块把它无损
升格为 ACGBlueprint：每个 step 变成一个 StepNode，相邻 step 之间连一条
DEPENDENCY 边。一条线性链就是一张最简单的 DAG，因此升格后的图可被
ACG 执行器以“就绪集调度”方式执行，行为与原线性执行完全一致。

这保证了存量工作流零改动接入新架构，是“静态优选、动态补位”里
“静态”一侧的落地基础。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agentos.core.acg.blueprint import ACGBlueprint
from agentos.core.acg.edges import ACGEdge
from agentos.core.acg.enums import ComplexityLevel, EdgeType
from agentos.core.acg.nodes import StepNode

if TYPE_CHECKING:
    from agentos.core.models.types import WorkflowDefinition


def _complexity_from_step_count(count: int) -> ComplexityLevel:
    if count <= 3:
        return ComplexityLevel.SIMPLE
    if count <= 7:
        return ComplexityLevel.MEDIUM
    if count <= 15:
        return ComplexityLevel.COMPLEX
    return ComplexityLevel.EXTREME


def promote_workflow_to_acg(
    workflow: "WorkflowDefinition",
    *,
    task_id: str | None = None,
) -> ACGBlueprint:
    """把线性 WorkflowDefinition 升格为等价的 ACGBlueprint。

    - 保留 step 顺序：用每个 step 的 stepId 作为 StepNode.node_id。
    - 依赖边：按 next_step_id 串联；若无显式 next，则按声明顺序串联。
    - reviewRequired 透传到 StepNode.review_required。
    """
    steps = list(workflow.steps)
    blueprint = ACGBlueprint(
        taskId=task_id,
        objective=workflow.description or workflow.name,
        complexityLevel=_complexity_from_step_count(len(steps)),
        metadata={
            "sourceWorkflowId": workflow.workflow_id,
            "promotedFromLinear": True,
            "runtimeEngine": workflow.effective_runtime_engine,
        },
    )

    for definition in steps:
        node = StepNode(
            nodeId=definition.step_id,
            name=definition.name,
            stepType="agent",
            goal=definition.name,
            agentName=definition.agent_name,
            capability=definition.capability,
            inputSpec=dict(definition.input),
            reviewRequired=definition.review_required,
            retryLimit=definition.max_retries,
        )
        blueprint.nodes.append(node)

    # 构建依赖边：优先用显式 next_step_id，回退到声明顺序。
    step_ids = {definition.step_id for definition in steps}
    for index, definition in enumerate(steps):
        target_id = definition.next_step_id
        if target_id in ("", "done", "completed", None):
            target_id = None
        if target_id is None and index + 1 < len(steps):
            target_id = steps[index + 1].step_id
        if target_id and target_id in step_ids:
            blueprint.edges.append(
                ACGEdge(
                    sourceId=definition.step_id,
                    targetId=target_id,
                    edgeType=EdgeType.DEPENDENCY,
                )
            )

    blueprint.touch()
    return blueprint


__all__ = ["promote_workflow_to_acg"]
