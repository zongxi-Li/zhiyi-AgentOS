from __future__ import annotations

import json

import pytest

from agentos.agents import AgentRegistry
from agentos.agents.base import AgentOutput, AgentProfile, BaseAgent
from agentos.core.acg.enums import ComplexityLevel
from agentos.core.models.types import WorkflowDefinition, WorkflowStepDefinition
from agentos.core.planning import (
    ACGPlanningError,
    CapabilityCatalog,
    IntentParser,
    PlanningCapabilityDescriptor,
    PlanningBudgetPolicy,
    PlanningEngine,
    PlanningRequestContext,
    build_material_context,
)
from agentos.core.planning.default_catalog import build_default_capability_catalog
from agentos.core.native import register_native_runtime
from agentos.core.workflow.registry import WorkflowRegistry


def test_short_material_is_preserved_and_long_material_is_bounded_deterministically():
    short = build_material_context(["短材料：风险与验证"])
    assert short.excerpt == "短材料：风险与验证"
    assert short.truncated is False

    long_text = "HEAD_MARKER" + "甲" * 7000 + "系统架构与安全风险" + "乙" * 9000 + "TAIL_MARKER"
    first = build_material_context([long_text], keywords=["系统架构", "安全风险"])
    second = build_material_context([long_text], keywords=["系统架构", "安全风险"])

    assert first == second
    assert first.truncated is True
    assert first.selected_characters <= 12_000
    assert first.digest
    assert first.summary_digest
    assert first.summary_digest != first.digest
    assert "HEAD_MARKER" in first.excerpt
    assert "系统架构与安全风险" in first.excerpt
    assert "TAIL_MARKER" in first.excerpt


def test_llm_outcome_preserves_authoritative_fields_and_records_rejections():
    class LLM:
        def generate_json(self, prompt, schema, **kwargs):
            assert "显式约束（必须保留）：不能停机" in prompt
            assert "任务材料" in prompt
            assert kwargs == {"thinking_mode": "deep", "temperature": 0.0, "timeout": 30.0}
            return {
                "data": {
                    "primaryGoal": "设计可靠系统",
                    "keyConstraints": ["模型约束"],
                    "requiredCapabilities": ["architecture_design", "不存在的能力"],
                    "expectedArtifacts": ["模型报告"],
                    "verificationRequirements": ["通过验收"],
                    "estimatedComplexity": "complex",
                },
                "provider": "test",
                "model": "planner",
                "latency_ms": 7,
            }

    catalog = build_default_capability_catalog()
    context = PlanningRequestContext.from_task_input(
        intent="升级核心系统",
        domain="general",
        task_type="general",
        task_input={
            "constraints": ["不能停机"],
            "expectedArtifacts": ["实施方案"],
            "materialText": "现有系统需要容灾和安全风险控制",
        },
        capability_catalog=catalog,
    )
    outcome = IntentParser(LLM(), catalog).parse_outcome(
        intent=context.intent,
        domain=context.domain,
        task_type=context.task_type,
        thinking_mode="deep",
        context=context,
    )

    assert outcome.source == "llm"
    assert outcome.fallback_reason is None
    assert outcome.rejected_capabilities == ("不存在的能力",)
    assert outcome.llm_metadata == {"provider": "test", "model": "planner", "latency_ms": 7}
    assert outcome.profile.key_constraints == ["不能停机", "模型约束"]
    assert outcome.profile.expected_artifacts == ["实施方案", "模型报告"]
    assert "artifact_generation" in outcome.profile.required_capabilities
    assert "verification" in outcome.profile.required_capabilities


@pytest.mark.parametrize(
    ("failure", "reason"),
    [
        (TimeoutError("timed out"), "llm_timeout"),
        (RuntimeError("provider request timed out"), "llm_timeout"),
        (ValueError("invalid json"), "llm_invalid_response"),
    ],
)
def test_llm_failures_use_auditable_heuristic_fallback(failure, reason):
    class LLM:
        def generate_json(self, prompt, schema, **kwargs):
            raise failure

    outcome = IntentParser(LLM()).parse_outcome(
        intent="分析风险并生成报告",
        domain="general",
        task_type="general",
    )

    assert outcome.source == "heuristic"
    assert outcome.fallback_reason == reason
    assert outcome.profile.required_capabilities


def test_llm_all_unknown_capabilities_are_audited_before_fallback():
    class LLM:
        def generate_json(self, prompt, schema, **kwargs):
            return {
                "data": {
                    "primaryGoal": "处理任务",
                    "requiredCapabilities": ["unregistered_alpha", "unregistered_beta"],
                    "estimatedComplexity": "medium",
                }
            }

    outcome = IntentParser(LLM()).parse_outcome(
        intent="分析任务并输出报告",
        domain="general",
        task_type="general",
    )

    assert outcome.source == "heuristic"
    assert outcome.fallback_reason == "llm_no_registered_capability"
    assert outcome.rejected_capabilities == (
        "unregistered_alpha",
        "unregistered_beta",
    )


def test_material_excerpt_is_not_persisted_in_planning_decision():
    secret = "PRIVATE_MATERIAL_SENTINEL"
    catalog = build_default_capability_catalog()
    agents = AgentRegistry()
    workflows = WorkflowRegistry()
    register_native_runtime(agent_registry=agents, workflow_registry=workflows)
    context = PlanningRequestContext.from_task_input(
        intent="分析任务",
        domain="general",
        task_type="general",
        task_input={"materialText": f"风险分析 {secret} 最终报告"},
        capability_catalog=catalog,
    )
    plan = PlanningEngine(
        workflow_registry=workflows,
        agent_registry=agents,
        capability_catalog=catalog,
    ).plan(
        task_id="privacy",
        intent=context.intent,
        domain="general",
        task_type="general",
        force_dynamic=True,
        deterministic_intent=True,
        planning_context=context,
    )

    persisted = json.dumps(
        {"decision": plan.to_decision(), "metadata": plan.blueprint.metadata},
        ensure_ascii=False,
    )
    assert secret not in persisted
    assert plan.material_context["digest"]
    assert plan.material_context["selectedCharacters"] > 0


def test_budget_policy_defaults_and_rejects_invalid_override(monkeypatch):
    policy = PlanningBudgetPolicy.from_env()
    assert policy.for_complexity(ComplexityLevel.SIMPLE) == 2048
    assert policy.for_complexity(ComplexityLevel.EXTREME) == 16384

    monkeypatch.setenv("AGENTOS_PLANNING_ENTROPY_SIMPLE", "0")
    with pytest.raises(ValueError, match="positive integer"):
        PlanningBudgetPolicy.from_env()


class _BudgetAgent(BaseAgent):
    async def run(self, context):
        return AgentOutput(output={})


class _BudgetLLM:
    def generate_json(self, prompt, schema, **kwargs):
        return {
            "data": {
                "primaryGoal": "完成双能力任务",
                "requiredCapabilities": ["cap_a", "cap_b"],
                "estimatedComplexity": "simple",
                "domainHint": "general",
                "taskTypeHint": "general",
            }
        }


def _budget_engine(limit: int, *, extra_template_agent: bool = False) -> PlanningEngine:
    catalog = CapabilityCatalog(
        [
            PlanningCapabilityDescriptor(
                capabilityId="cap_a",
                displayName="能力 A",
                planningStage="understand",
            ),
            PlanningCapabilityDescriptor(
                capabilityId="cap_b",
                displayName="能力 B",
                planningStage="deliver",
                dependsOn=["cap_a"],
                producesArtifact=True,
            ),
        ]
    )
    catalog.validate()
    agents = AgentRegistry()
    agents.register(
        _BudgetAgent(
            AgentProfile(agentName="agent_a", domain="general", capabilities=["cap_a"])
        )
    )
    agents.register(
        _BudgetAgent(
            AgentProfile(agentName="agent_b", domain="general", capabilities=["cap_b"])
        )
    )
    template_steps = [
        WorkflowStepDefinition(
            stepId="a",
            name="A",
            agentName="agent_a",
            capability="cap_a",
        ),
        WorkflowStepDefinition(
            stepId="b",
            name="B",
            agentName="agent_b",
            capability="cap_b",
        ),
    ]
    if extra_template_agent:
        agents.register(
            _BudgetAgent(
                AgentProfile(
                    agentName="agent_c",
                    domain="general",
                    capabilities=["cap_b"],
                    bindingPriority=-1,
                )
            )
        )
        template_steps.append(
            WorkflowStepDefinition(
                stepId="c",
                name="C",
                agentName="agent_c",
                capability="cap_b",
            )
        )
    workflows = WorkflowRegistry()
    workflows.register(
        WorkflowDefinition(
            workflowId="two_agent_template",
            name="双 Agent 模板",
            domain="general",
            intent="general",
            runtimeEngine="acg",
            description="完成双能力任务 cap_a cap_b",
            tags=["cap_a", "cap_b"],
            steps=template_steps,
        )
    )
    policy = PlanningBudgetPolicy(
        {
            ComplexityLevel.SIMPLE: limit,
            ComplexityLevel.MEDIUM: limit,
            ComplexityLevel.COMPLEX: limit,
            ComplexityLevel.EXTREME: limit,
        }
    )
    return PlanningEngine(
        workflow_registry=workflows,
        agent_registry=agents,
        capability_catalog=catalog,
        intent_llm=_BudgetLLM(),
        budget_policy=policy,
    )


def test_entropy_budget_boundary_allows_template_and_overflow_fails_explicitly():
    accepted = _budget_engine(256).plan(
        task_id="budget-boundary",
        intent="完成双能力任务",
        requested_planning_mode="template_preferred",
    )
    assert accepted.strategy == "static_template"
    assert accepted.estimated_entropy == accepted.entropy_budget == 256

    with pytest.raises(ACGPlanningError) as error:
        _budget_engine(255).plan(
            task_id="budget-overflow",
            intent="完成双能力任务",
            requested_planning_mode="template_preferred",
        )
    assert error.value.code == "PLANNING_BUDGET_EXCEEDED"


def test_over_budget_template_falls_back_to_a_dynamic_graph_within_budget():
    result = _budget_engine(256, extra_template_agent=True).plan(
        task_id="template-budget-fallback",
        intent="完成双能力任务",
        requested_planning_mode="template_preferred",
    )

    assert result.strategy == "dynamic_generation"
    assert result.estimated_entropy == result.entropy_budget == 256
    assert any("template entropy" in note for note in result.notes)
