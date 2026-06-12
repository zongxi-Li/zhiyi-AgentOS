"""认知规划引擎子系统（设计书 §2.1）。

把高维模糊的自然语言意图，转化为可执行的 ACG 蓝图。
采用“静态优选，动态补位”：优先复用验证过的模板，无命中时由认知路由 +
ACG 构建器动态生成认知协作网络。
"""

from __future__ import annotations

from agentos.core.planning.acg_builder import ACGBuilder
from agentos.core.planning.cognitive_router import (
    CapabilityBinding,
    CognitiveRouter,
    CollaborationNetwork,
)
from agentos.core.planning.engine import PlanningEngine, PlanResult
from agentos.core.planning.intent_parser import IntentLLM, IntentParser
from agentos.core.planning.profile import TaskSemanticProfile
from agentos.core.planning.template_matcher import TemplateMatch, TemplateMatcher

__all__ = [
    "PlanningEngine",
    "PlanResult",
    "IntentParser",
    "IntentLLM",
    "TaskSemanticProfile",
    "TemplateMatcher",
    "TemplateMatch",
    "CognitiveRouter",
    "CollaborationNetwork",
    "CapabilityBinding",
    "ACGBuilder",
]
