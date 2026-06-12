"""ACG 构建器（设计书 §2.1「ACG构建器」）。

把意图画像 + 认知路由的协作网络物化为可执行的 ACGBlueprint：
1. 任务目标分解 → 步骤序列（按能力顺序，复杂度控制粒度）
2. 实例化 StepNode，绑定 assigned_agent
3. 赋能节点注入：阶段性结论后注入 Memory 节点；需外部依据的步骤注入
   Evidence 节点
4. 建立依赖主干 + write/read/support 边
5. 图级验证：环检测 + 悬空依赖检查

这是“动态补位”一侧：无模板命中时由本构建器动态生成 ACG。
"""

from __future__ import annotations

from typing import List

from agentos.core.acg import (
    ACGBlueprint,
    ACGEdge,
    ComplexityLevel,
    EdgeType,
    EvidenceNode,
    MemoryNode,
    StepNode,
    validate_blueprint,
)
from agentos.core.acg.nodes import _node_id
from agentos.core.planning.cognitive_router import CollaborationNetwork
from agentos.core.planning.profile import TaskSemanticProfile

# 需要证据支撑的能力（产出结论性内容，须可审计）
_EVIDENCE_CAPABILITIES = {"风险识别", "证据检索", "报告生成", "需求分析"}
# 产生阶段性结论、值得写入记忆的能力
_MEMORY_CAPABILITIES = {"风险识别", "需求分析", "报告生成"}


class ACGBuilder:
    """动态 ACG 蓝图构建器。"""

    def build(
        self,
        *,
        task_id: str,
        profile: TaskSemanticProfile,
        network: CollaborationNetwork,
    ) -> ACGBlueprint:
        blueprint = ACGBlueprint(
            taskId=task_id,
            objective=profile.primary_goal,
            complexityLevel=profile.estimated_complexity,
            metadata={
                "generatedBy": "acg_builder",
                "domainHint": profile.domain_hint,
                "entropyBudget": profile.entropy_budget,
                "estimatedEntropy": network.estimated_entropy,
            },
        )

        # 1) 按能力顺序分解步骤，2) 实例化 StepNode 并绑定 Agent
        step_nodes: List[StepNode] = []
        for index, binding in enumerate(network.bindings):
            step = StepNode(
                nodeId=f"step_{index}_{_slug(binding.capability)}",
                name=binding.capability,
                goal=f"完成能力：{binding.capability}",
                agentName=binding.agent_name,
                capability=binding.capability,
                reviewRequired=(binding.capability == "报告生成" and profile.risk_level == "high"),
                metadata={"ephemeralAgent": binding.ephemeral},
            )
            blueprint.nodes.append(step)
            step_nodes.append(step)

        # 3) 依赖主干：线性串联（后续可由依赖分析升级为并行/分支）
        for i in range(len(step_nodes) - 1):
            blueprint.edges.append(
                ACGEdge(
                    sourceId=step_nodes[i].node_id,
                    targetId=step_nodes[i + 1].node_id,
                    edgeType=EdgeType.DEPENDENCY,
                )
            )

        # 4) 赋能节点注入
        for step in step_nodes:
            cap = step.capability or ""
            if cap in _EVIDENCE_CAPABILITIES:
                ev = EvidenceNode(nodeId=_node_id("ev"), name=f"证据:{cap}", evidenceType="retrieved")
                blueprint.nodes.append(ev)
                blueprint.edges.append(
                    ACGEdge(sourceId=ev.node_id, targetId=step.node_id, edgeType=EdgeType.SUPPORT)
                )
                step.evidence_ids.append(ev.node_id)
            if cap in _MEMORY_CAPABILITIES:
                mem = MemoryNode(nodeId=_node_id("mem"), name=f"记忆:{cap}", memoryType="episodic")
                blueprint.nodes.append(mem)
                blueprint.edges.append(
                    ACGEdge(sourceId=step.node_id, targetId=mem.node_id, edgeType=EdgeType.WRITE)
                )
                step.memory_ids.append(mem.node_id)

        blueprint.touch()
        # 5) 图级验证（环检测 + 悬空依赖）
        validate_blueprint(blueprint)
        return blueprint


def _slug(text: str) -> str:
    return "".join(c for c in (text or "") if c.isalnum())[:12] or "cap"


__all__ = ["ACGBuilder"]
