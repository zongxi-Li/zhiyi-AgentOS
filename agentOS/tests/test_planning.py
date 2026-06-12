"""认知规划引擎契约测试。

锁定不变量：意图解析画像、模板匹配阈值命中走静态、无命中走动态生成、
动态 ACG 含赋能节点注入且图合法。
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from agentos.agents import AgentRegistry
from agentos.agents.base import AgentOutput, AgentProfile, BaseAgent
from agentos.core.acg import NodeType, validate_blueprint
from agentos.core.acg.enums import ComplexityLevel
from agentos.core.models.types import WorkflowDefinition
from agentos.core.planning import IntentParser, PlanningEngine, TaskSemanticProfile
from agentos.core.planning.cognitive_router import CognitiveRouter
from agentos.core.planning.template_matcher import TemplateMatcher
from agentos.core.workflow.registry import WorkflowRegistry


class _Agent(BaseAgent):
    def __init__(self, name, domain, caps):
        super().__init__(AgentProfile(agentName=name, domain=domain, capabilities=caps))

    async def run(self, context):
        return AgentOutput(output={}, summary="ok")


def _registries():
    wr = WorkflowRegistry()
    wr.register(
        WorkflowDefinition(
            workflowId="legal_contract_review_v1",
            name="合同审查",
            domain="legal",
            intent="contract_review",
            description="标准合同审查流程：解析、风险、证据、报告",
            steps=[
                {"stepId": "parse", "name": "解析", "agentName": "parse", "nextStepId": "risk"},
                {"stepId": "risk", "name": "风险", "agentName": "risk"},
            ],
        )
    )
    ar = AgentRegistry()
    ar.register(_Agent("parser", "legal", ["文本解析"]))
    ar.register(_Agent("risk", "legal", ["风险识别"]))
    ar.register(_Agent("reporter", "legal", ["报告生成"]))
    return wr, ar


# ---------- 意图解析 ----------
def test_intent_parser_heuristic_extracts_capabilities():
    parser = IntentParser()  # 无 LLM，走启发式
    profile = parser.parse(intent="审查合同违约风险并生成报告", domain="legal", task_type="contract_review")
    assert isinstance(profile, TaskSemanticProfile)
    assert profile.domain_hint == "legal"
    assert "风险识别" in profile.required_capabilities
    assert "报告生成" in profile.required_capabilities
    assert profile.risk_level == "high"  # 含“风险/违约”


def test_intent_parser_uses_injected_llm():
    class _LLM:
        def generate_json(self, prompt, schema, **kwargs):
            return {
                "data": {
                    "primaryGoal": "LLM目标",
                    "requiredCapabilities": ["代码生成"],
                    "estimatedComplexity": "complex",
                }
            }

    profile = IntentParser(_LLM()).parse(intent="x", domain="programmer", task_type="impl")
    assert profile.primary_goal == "LLM目标"
    assert profile.required_capabilities == ["代码生成"]
    assert profile.estimated_complexity == ComplexityLevel.COMPLEX


def test_intent_parser_falls_back_when_llm_raises():
    class _BadLLM:
        def generate_json(self, prompt, schema, **kwargs):
            raise RuntimeError("llm down")

    profile = IntentParser(_BadLLM()).parse(intent="审查合同", domain="legal", task_type="contract_review")
    assert profile.primary_goal  # 回退启发式成功


# ---------- 模板匹配 ----------
def test_template_matcher_exact_intent_hits():
    wr, _ = _registries()
    matcher = TemplateMatcher(wr, threshold=0.85)
    profile = TaskSemanticProfile(primaryGoal="审查合同", domainHint="legal", taskTypeHint="contract_review")
    match = matcher.match(profile)
    assert matcher.is_hit(match)
    assert match.workflow.workflow_id == "legal_contract_review_v1"


def test_template_matcher_no_domain_returns_none():
    wr, _ = _registries()
    matcher = TemplateMatcher(wr)
    profile = TaskSemanticProfile(primaryGoal="x", domainHint="aerospace", taskTypeHint="design")
    match = matcher.match(profile)
    assert not matcher.is_hit(match)


# ---------- 端到端规划 ----------
def test_plan_static_template_path():
    wr, ar = _registries()
    engine = PlanningEngine(workflow_registry=wr, agent_registry=ar)
    result = engine.plan(
        task_id="t1", intent="审查这份采购合同的违约风险", domain="legal", task_type="contract_review"
    )
    assert result.strategy == "static_template"
    assert result.template_id == "legal_contract_review_v1"
    validate_blueprint(result.blueprint)
    assert all(n.node_type == NodeType.STEP for n in result.blueprint.nodes)


def test_plan_dynamic_generation_path():
    wr, ar = _registries()
    engine = PlanningEngine(workflow_registry=wr, agent_registry=ar)
    result = engine.plan(
        task_id="t2",
        intent="分析跨境并购的税务合规与风险并生成报告",
        domain="legal",
        task_type="ma_tax_analysis",
    )
    assert result.strategy == "dynamic_generation"
    validate_blueprint(result.blueprint)
    # 动态图应注入赋能节点（Evidence/Memory）
    node_types = {n.node_type for n in result.blueprint.nodes}
    assert NodeType.STEP in node_types
    assert NodeType.EVIDENCE in node_types or NodeType.MEMORY in node_types


def test_cognitive_router_binds_capabilities():
    _, ar = _registries()
    router = CognitiveRouter(ar)
    profile = TaskSemanticProfile(
        primaryGoal="x",
        requiredCapabilities=["文本解析", "风险识别", "未知能力"],
        domainHint="legal",
    )
    network = router.route(profile, domain="legal")
    assert len(network.bindings) == 3
    # 已知能力绑定到真实 agent；未知能力触发临时角色
    ephemeral = [b for b in network.bindings if b.ephemeral]
    assert len(ephemeral) == 1
    assert ephemeral[0].capability == "未知能力"
