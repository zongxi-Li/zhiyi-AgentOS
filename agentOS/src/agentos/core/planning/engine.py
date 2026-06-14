"""认知规划引擎（设计书 §2.1）。

“静态优选，动态补位”混合策略的总编排：

  意图解析 → 模板匹配
     ├─ 命中(≥阈值) → 复用模板，线性升格为 ACG（静态，零规划开销）
     └─ 未命中     → 认知路由 → ACG 构建器（动态生成 ACG）

产物统一为 ACGBlueprint，交付执行器。规划决策（走静态还是动态、命中哪个
模板、能力如何绑定）记录在 PlanResult，供审计与前端展示。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from agentos.agents import AgentRegistry
from agentos.core.acg import ACGBlueprint, promote_workflow_to_acg
from agentos.core.planning.acg_builder import ACGBuilder
from agentos.core.planning.cognitive_router import CognitiveRouter
from agentos.core.planning.intent_parser import IntentLLM, IntentParser
from agentos.core.planning.profile import TaskSemanticProfile
from agentos.core.planning.template_matcher import TemplateMatcher
from agentos.core.workflow.registry import WorkflowRegistry


@dataclass
class PlanResult:
    blueprint: ACGBlueprint
    profile: TaskSemanticProfile
    strategy: str  # "static_template" | "dynamic_generation"
    template_id: Optional[str] = None
    template_score: float = 0.0
    notes: list[str] = field(default_factory=list)

    def to_decision(self) -> Dict[str, Any]:
        return {
            "strategy": self.strategy,
            "templateId": self.template_id,
            "templateScore": self.template_score,
            "profile": self.profile.model_dump(by_alias=True),
            "graphId": self.blueprint.graph_id,
            "nodeCount": self.blueprint.node_count,
            "edgeCount": self.blueprint.edge_count,
            "notes": self.notes,
        }


class PlanningEngine:
    """认知规划引擎。"""

    def __init__(
        self,
        *,
        workflow_registry: WorkflowRegistry,
        agent_registry: AgentRegistry,
        intent_llm: Optional[IntentLLM] = None,
        template_threshold: float = 0.85,
    ):
        self.intent_parser = IntentParser(intent_llm)
        self.template_matcher = TemplateMatcher(workflow_registry, threshold=template_threshold)
        self.cognitive_router = CognitiveRouter(agent_registry)
        self.acg_builder = ACGBuilder()

    def plan(
        self,
        *,
        task_id: str,
        intent: str,
        domain: str = "general",
        task_type: str = "general",
        force_dynamic: bool = False,
    ) -> PlanResult:
        profile = self.intent_parser.parse(intent=intent, domain=domain, task_type=task_type)

        match = None
        if not force_dynamic:
            # 静态优选
            match = self.template_matcher.match(profile)
            if self.template_matcher.is_hit(match):
                blueprint = promote_workflow_to_acg(match.workflow, task_id=task_id)
                blueprint.objective = profile.primary_goal or blueprint.objective
                return PlanResult(
                    blueprint=blueprint,
                    profile=profile,
                    strategy="static_template",
                    template_id=match.workflow.workflow_id,
                    template_score=match.score,
                    notes=[f"matched template by {match.matched_by}"],
                )

        # 动态补位
        network = self.cognitive_router.route(profile, domain=domain)
        blueprint = self.acg_builder.build(task_id=task_id, profile=profile, network=network)
        notes = [
            "force dynamic planning; generated ACG dynamically"
            if force_dynamic
            else "no template hit; generated ACG dynamically"
        ]
        notes.extend(network.notes)
        return PlanResult(
            blueprint=blueprint,
            profile=profile,
            strategy="dynamic_generation",
            template_score=match.score if match else 0.0,
            notes=notes,
        )


__all__ = ["PlanningEngine", "PlanResult"]
