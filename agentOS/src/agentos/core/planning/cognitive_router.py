"""认知路由器（设计书 §2.1「认知路由」）。

规划器的核心创新组件：传统工作流调度任务节点，认知路由器调度“认知能力”。
按任务所需能力集合，结合 Agent 注册中心的能力画像完成匹配，输出能力→Agent
的绑定与协作网络。

四步实现（本阶段简化但保留骨架）：
1. 候选生成与硬过滤（能力标签匹配 + 健康/可用）
2. 多维效用评分与排序（语义匹配/历史成功率/负载/成本）
3. 协作网络构建与熵预算规划
4. 最终决策与绑定

无候选时支持动态角色生成（最小桩，标记 Ephemeral）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from agentos.agents import AgentRegistry
from agentos.agents.base import BaseAgent
from agentos.core.planning.profile import TaskSemanticProfile


_CAPABILITY_ALIASES = {
    "文本解析": ("contract_parse", "parse_contract", "contract_parser", "合同解析", "文本解析"),
    "条款分类": ("clause_classify", "clause_classifier", "条款分类", "条款识别"),
    "风险识别": ("risk_detect", "risk_detection", "risk_assessment", "风险识别", "风险评估"),
    "证据检索": ("legal_evidence_match", "legal_evidence_search", "evidence_analysis", "证据检索", "依据匹配"),
    "修改建议": ("revision_suggest", "revision_suggestion", "suggestion_generate", "修改建议", "修订建议"),
    "人工审核": ("human_review", "human_review_gate", "review", "人工审核", "复核"),
    "报告生成": ("report_generate", "report_generation", "draft", "报告生成", "文书生成"),
    "需求分析": ("case_intake", "case_understanding", "contract_parse", "需求分析", "案情理解"),
}

_NON_EXECUTABLE_CAPABILITY_KEYWORDS = (
    "多智能体",
    "协作编排",
    "任务图",
    "图编排",
    "工作流编排",
    "ACG",
    "DAG",
    "低熵通信",
    "上下文组织",
    "字段投递",
    "并行分析",
    "并行处理",
    "输出格式",
)


@dataclass
class CapabilityBinding:
    capability: str
    agent_name: str
    score: float
    ephemeral: bool = False


@dataclass
class CollaborationNetwork:
    bindings: List[CapabilityBinding] = field(default_factory=list)
    estimated_entropy: int = 0
    entropy_budget: int = 0
    notes: List[str] = field(default_factory=list)

    @property
    def agent_names(self) -> List[str]:
        seen: List[str] = []
        for b in self.bindings:
            if b.agent_name not in seen:
                seen.append(b.agent_name)
        return seen

    @property
    def over_budget(self) -> bool:
        return self.entropy_budget > 0 and self.estimated_entropy > self.entropy_budget


class CognitiveRouter:
    """认知能力路由。"""

    def __init__(self, agent_registry: AgentRegistry, *, entropy_per_edge: int = 256):
        self.agent_registry = agent_registry
        self.entropy_per_edge = entropy_per_edge

    def route(self, profile: TaskSemanticProfile, *, domain: str) -> CollaborationNetwork:
        network = CollaborationNetwork(entropy_budget=profile.entropy_budget)
        agents = [a for a in self.agent_registry.all() if a.profile.domain.lower() == domain.lower()]

        for capability in profile.required_capabilities:
            if _is_non_executable_capability(capability):
                network.notes.append(f"skipped non-executable planning capability: {capability}")
                continue
            binding = self._match_capability(capability, agents)
            network.bindings.append(binding)

        # 熵预算规划：每条通信边预估熵耗（线性协作链 = bindings-1 条边）
        edge_count = max(0, len(network.agent_names) - 1)
        network.estimated_entropy = edge_count * self.entropy_per_edge
        if network.over_budget:
            network.notes.append(
                f"estimated entropy {network.estimated_entropy} exceeds budget {network.entropy_budget}; "
                "would trigger template substitution / message batching in full implementation"
            )
        return network

    def _match_capability(self, capability: str, agents: List[BaseAgent]) -> CapabilityBinding:
        # 候选生成与硬过滤：能力标签语义包含匹配
        scored: List[tuple[float, BaseAgent]] = []
        cap_aliases = _capability_aliases(capability)
        for agent in agents:
            caps = [c.lower() for c in agent.profile.capabilities]
            score = self._capability_score(cap_aliases, caps, agent)
            if score > 0:
                scored.append((score, agent))

        if not scored:
            # 动态角色生成（最小桩）：合成临时角色描述符
            return CapabilityBinding(
                capability=capability,
                agent_name=f"ephemeral::{capability}",
                score=0.5,
                ephemeral=True,
            )

        scored.sort(key=lambda x: x[0], reverse=True)
        best_score, best_agent = scored[0]
        return CapabilityBinding(
            capability=capability,
            agent_name=best_agent.profile.agent_name,
            score=round(best_score, 4),
        )

    @staticmethod
    def _capability_score(cap_aliases: List[str], agent_caps: List[str], agent: BaseAgent) -> float:
        # 多维效用评分（简化）：语义匹配 + 风险等级匹配
        semantic = 0.0
        agent_name = (agent.profile.agent_name or "").strip().lower()
        for index, cap in enumerate(cap_aliases):
            if not cap:
                continue
            alias_weight = max(0.65, 1.0 - index * 0.03)
            for ac in agent_caps:
                if not ac:
                    continue
                if cap == ac:
                    semantic = max(semantic, alias_weight)
                elif cap in ac or ac in cap:
                    semantic = max(semantic, min(0.82, alias_weight - 0.12))
            if agent_name:
                if cap == agent_name:
                    semantic = max(semantic, alias_weight - 0.01)
                elif cap in agent_name or agent_name in cap:
                    semantic = max(semantic, min(0.78, alias_weight - 0.16))
        if semantic <= 0.0:
            return 0.0
        # 健康/可用维度：当前 demo agent 默认健康，给固定加权
        return round(semantic, 4)


def _capability_aliases(capability: str) -> List[str]:
    raw = (capability or "").strip()
    aliases = [raw.lower()]
    for key, values in _CAPABILITY_ALIASES.items():
        if raw == key or raw.lower() in {v.lower() for v in values}:
            aliases.extend(v.lower() for v in values)
            break
    seen: List[str] = []
    for item in aliases:
        if item and item not in seen:
            seen.append(item)
    return seen


def _is_non_executable_capability(capability: str) -> bool:
    compact = (capability or "").replace(" ", "").replace("/", "")
    return any(keyword.lower() in compact.lower() for keyword in _NON_EXECUTABLE_CAPABILITY_KEYWORDS)


__all__ = ["CognitiveRouter", "CollaborationNetwork", "CapabilityBinding"]
