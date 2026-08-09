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
import random
import secrets
from typing import Any, Dict, Optional

from agentos.agents import AgentRegistry
from agentos.core.acg import ACGBlueprint, promote_workflow_to_acg
from agentos.core.planning.acg_builder import ACGBuilder
from agentos.core.planning.budget import PlanningBudgetPolicy
from agentos.core.planning.capabilities import CapabilityCatalog
from agentos.core.planning.context import PlanningRequestContext
from agentos.core.planning.cognitive_router import CognitiveRouter
from agentos.core.planning.default_catalog import build_default_capability_catalog
from agentos.core.planning.intent_parser import INTENT_PROMPT_VERSION, IntentLLM, IntentParser
from agentos.core.planning.profile import TaskSemanticProfile
from agentos.core.planning.template_matcher import TemplateMatcher
from agentos.core.planning.variants import (
    PLANNER_ALGORITHM_VERSION,
    PlanningDiversity,
    PlanningVariantGenerator,
    normalize_planning_diversity,
)
from agentos.core.workflow.registry import WorkflowRegistry


class ACGPlanningError(ValueError):
    """The planner cannot produce an executable ACG with current capabilities/budgets."""

    def __init__(self, message: str, *, code: str = "ACG_PLANNING_FAILED") -> None:
        super().__init__(message)
        self.code = code


@dataclass
class PlanResult:
    blueprint: ACGBlueprint
    profile: TaskSemanticProfile
    strategy: str  # "static_template" | "dynamic_generation"
    template_id: Optional[str] = None
    template_score: float = 0.0
    thinking_mode: Optional[str] = None
    planning_diversity: PlanningDiversity = "stable"
    planning_seed: Optional[int] = None
    planner_algorithm_version: str = PLANNER_ALGORITHM_VERSION
    capability_catalog_revision: Optional[str] = None
    candidate_count: int = 1
    selected_variant_id: Optional[str] = None
    selected_capabilities: list[str] = field(default_factory=list)
    selected_bindings: list[Dict[str, str]] = field(default_factory=list)
    selection_reasons: list[str] = field(default_factory=list)
    stochastic_fallback: bool = False
    requested_planning_mode: str = "template_preferred"
    intent_parse_source: str = "heuristic"
    intent_fallback_reason: Optional[str] = None
    rejected_capabilities: list[str] = field(default_factory=list)
    material_context: Dict[str, Any] = field(default_factory=dict)
    estimated_entropy: int = 0
    entropy_budget: int = 0
    intent_llm_metadata: Dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def to_diagnostics(self) -> Dict[str, Any]:
        return {
            "requestedPlanningMode": self.requested_planning_mode,
            "effectiveStrategy": self.strategy,
            "intentParseSource": self.intent_parse_source,
            "intentFallbackReason": self.intent_fallback_reason,
            "templateId": self.template_id,
            "templateScore": self.template_score,
            "materialContext": dict(self.material_context),
            "rejectedCapabilities": list(self.rejected_capabilities),
            "entropyBudget": self.entropy_budget,
            "estimatedEntropy": self.estimated_entropy,
            "intentPromptVersion": INTENT_PROMPT_VERSION,
            "intentProvider": self.intent_llm_metadata.get("provider"),
            "intentModel": self.intent_llm_metadata.get("model"),
            "intentLatencyMs": self.intent_llm_metadata.get("latency_ms"),
        }

    def to_decision(self) -> Dict[str, Any]:
        return {
            "strategy": self.strategy,
            "templateId": self.template_id,
            "templateScore": self.template_score,
            "thinkingMode": self.thinking_mode,
            "planningDiversity": self.planning_diversity,
            "planningSeed": self.planning_seed,
            "plannerAlgorithmVersion": self.planner_algorithm_version,
            "capabilityCatalogRevision": self.capability_catalog_revision,
            "candidateCount": self.candidate_count,
            "selectedVariantId": self.selected_variant_id,
            "selectedCapabilities": self.selected_capabilities,
            "selectedBindings": self.selected_bindings,
            "selectionReasons": self.selection_reasons,
            "stochasticFallback": self.stochastic_fallback,
            "planningDiagnostics": self.to_diagnostics(),
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
        capability_catalog: CapabilityCatalog | None = None,
        intent_llm: Optional[IntentLLM] = None,
        template_threshold: float = 0.85,
        budget_policy: PlanningBudgetPolicy | None = None,
    ):
        self.capability_catalog = capability_catalog or build_default_capability_catalog()
        self.intent_parser = IntentParser(intent_llm, self.capability_catalog)
        self.template_matcher = TemplateMatcher(workflow_registry, threshold=template_threshold)
        self.cognitive_router = CognitiveRouter(agent_registry, self.capability_catalog)
        self.acg_builder = ACGBuilder(self.capability_catalog)
        self.budget_policy = budget_policy or PlanningBudgetPolicy.from_env()
        self.variant_generator = PlanningVariantGenerator(
            capability_catalog=self.capability_catalog,
            cognitive_router=self.cognitive_router,
        )

    def plan(
        self,
        *,
        task_id: str,
        intent: str,
        domain: str = "general",
        task_type: str = "general",
        force_dynamic: bool = False,
        thinking_mode: str | None = None,
        deterministic_intent: bool = False,
        planning_diversity: str = "stable",
        planning_seed: int | None = None,
        capability_catalog_revision: str | None = None,
        planning_context: PlanningRequestContext | None = None,
        requested_planning_mode: str | None = None,
        explicit_template_id: str | None = None,
    ) -> PlanResult:
        diversity = normalize_planning_diversity(planning_diversity)
        resolved_seed = planning_seed
        if diversity != "stable" and resolved_seed is None:
            resolved_seed = secrets.randbits(53)
        context = planning_context or PlanningRequestContext(
            intent=intent,
            domain=domain,
            task_type=task_type,
        )
        parse_outcome = self.intent_parser.parse_outcome(
            intent=intent,
            domain=domain,
            task_type=task_type,
            thinking_mode=thinking_mode,
            use_llm=not deterministic_intent,
            context=context,
        )
        profile = parse_outcome.profile
        profile.entropy_budget = self.budget_policy.for_complexity(
            profile.estimated_complexity
        )
        mode_was_explicit = requested_planning_mode is not None
        mode = requested_planning_mode or (
            "dynamic" if force_dynamic else "template_preferred"
        )

        match = None
        template_budget_rejection: str | None = None
        should_try_template = not force_dynamic and (
            bool(explicit_template_id)
            or diversity == "stable"
            or (mode_was_explicit and mode == "template_preferred")
        )
        if should_try_template:
            # 静态优选
            match = (
                self.template_matcher.explicit(explicit_template_id)
                if explicit_template_id
                else self.template_matcher.match(profile)
            )
            if self.template_matcher.is_hit(match):
                blueprint = promote_workflow_to_acg(match.workflow, task_id=task_id)
                blueprint.objective = profile.primary_goal or blueprint.objective
                estimated_entropy = self._estimate_blueprint_entropy(blueprint)
                if estimated_entropy <= profile.entropy_budget:
                    result = PlanResult(
                        blueprint=blueprint,
                        profile=profile,
                        strategy="static_template",
                        template_id=match.workflow.workflow_id,
                        template_score=match.score,
                        thinking_mode=thinking_mode,
                        planning_diversity=diversity,
                        planning_seed=resolved_seed,
                        capability_catalog_revision=capability_catalog_revision,
                        selected_capabilities=list(profile.required_capabilities),
                        requested_planning_mode=mode,
                        intent_parse_source=parse_outcome.source,
                        intent_fallback_reason=parse_outcome.fallback_reason,
                        rejected_capabilities=list(parse_outcome.rejected_capabilities),
                        material_context=context.material.to_diagnostics(),
                        estimated_entropy=estimated_entropy,
                        entropy_budget=profile.entropy_budget,
                        intent_llm_metadata=dict(parse_outcome.llm_metadata),
                        notes=[f"matched template by {match.matched_by}"],
                    )
                    self._decorate_blueprint(result)
                    return result
                if explicit_template_id:
                    raise ACGPlanningError(
                        f"Explicit workflow entropy {estimated_entropy} exceeds budget "
                        f"{profile.entropy_budget}",
                        code="PLANNING_BUDGET_EXCEEDED",
                    )
                template_budget_rejection = (
                    f"template entropy {estimated_entropy} exceeds budget "
                    f"{profile.entropy_budget}; trying dynamic planning"
                )

        # 动态补位
        stable_network = self.cognitive_router.route(profile, domain=domain)
        if stable_network.unresolved_capabilities:
            raise ACGPlanningError(
                "No registered Agent can execute capabilities: "
                + ", ".join(stable_network.unresolved_capabilities),
                code="PLANNING_CAPABILITY_UNRESOLVED",
            )
        if stable_network.over_budget:
            raise ACGPlanningError(
                f"Estimated entropy {stable_network.estimated_entropy} exceeds budget "
                f"{stable_network.entropy_budget}",
                code="PLANNING_BUDGET_EXCEEDED",
            )
        variant_set = self.variant_generator.generate(
            profile=profile,
            domain=domain,
            diversity=diversity,
            seed=resolved_seed,
        )
        valid: list[tuple[Any, ACGBlueprint]] = []
        rejected: list[str] = []
        for variant in variant_set.variants:
            if variant.network.unresolved_capabilities or variant.network.over_budget:
                rejected.append(f"{variant.variant_id}: unresolved capability or entropy budget")
                continue
            try:
                candidate = self.acg_builder.build(
                    task_id=task_id,
                    profile=profile,
                    network=variant.network,
                    variant=variant,
                )
                self._validate_agents(candidate, domain=domain)
            except (KeyError, ValueError) as exc:
                rejected.append(f"{variant.variant_id}: {exc}")
                continue
            valid.append((variant, candidate))

        stochastic_fallback = False
        if valid:
            selection_random = random.Random(resolved_seed)
            selected_index = selection_random.randrange(len(valid)) if len(valid) > 1 else 0
            selected_variant, blueprint = valid[selected_index]
        else:
            stochastic_fallback = diversity != "stable"
            stable_set = self.variant_generator.generate(
                profile=profile,
                domain=domain,
                diversity="stable",
                seed=None,
            )
            selected_variant = stable_set.variants[0]
            if selected_variant.network.over_budget:
                raise ACGPlanningError(
                    f"Estimated entropy {selected_variant.network.estimated_entropy} exceeds "
                    f"budget {selected_variant.network.entropy_budget}",
                    code="PLANNING_BUDGET_EXCEEDED",
                )
            blueprint = self.acg_builder.build(
                task_id=task_id,
                profile=profile,
                network=selected_variant.network,
                variant=selected_variant,
            )
            self._validate_agents(blueprint, domain=domain)
            valid = [(selected_variant, blueprint)]

        blueprint.metadata.update(
            {
                "planningDiversity": diversity,
                "planningSeed": resolved_seed,
                "plannerAlgorithmVersion": PLANNER_ALGORITHM_VERSION,
                "capabilityCatalogRevision": capability_catalog_revision,
                "candidateCount": len(valid),
                "selectedVariantId": selected_variant.variant_id,
            }
        )
        notes = [
            "force dynamic planning; generated ACG dynamically"
            if force_dynamic
            else "stochastic planning requested; generated ACG dynamically"
            if diversity != "stable"
            else "no template hit; generated ACG dynamically"
        ]
        notes.extend(selected_variant.network.notes)
        notes.extend(rejected)
        if template_budget_rejection:
            notes.append(template_budget_rejection)
        result = PlanResult(
            blueprint=blueprint,
            profile=profile,
            strategy="dynamic_generation",
            template_score=match.score if match else 0.0,
            thinking_mode=thinking_mode,
            planning_diversity=diversity,
            planning_seed=resolved_seed,
            capability_catalog_revision=capability_catalog_revision,
            candidate_count=len(valid),
            selected_variant_id=selected_variant.variant_id,
            selected_capabilities=list(profile.required_capabilities),
            selected_bindings=[
                {
                    "capabilityId": binding.capability,
                    "agentName": binding.agent_name,
                }
                for binding in selected_variant.network.bindings
            ],
            selection_reasons=list(selected_variant.selection_reasons),
            stochastic_fallback=stochastic_fallback,
            requested_planning_mode=mode,
            intent_parse_source=parse_outcome.source,
            intent_fallback_reason=parse_outcome.fallback_reason,
            rejected_capabilities=list(parse_outcome.rejected_capabilities),
            material_context=context.material.to_diagnostics(),
            estimated_entropy=selected_variant.network.estimated_entropy,
            entropy_budget=profile.entropy_budget,
            intent_llm_metadata=dict(parse_outcome.llm_metadata),
            notes=notes,
        )
        self._decorate_blueprint(result)
        return result

    def _decorate_blueprint(self, result: PlanResult) -> None:
        result.blueprint.metadata.update(
            {
                "semanticProfile": result.profile.model_dump(
                    by_alias=True,
                    mode="json",
                ),
                "planningDiagnostics": result.to_diagnostics(),
                "plannerAlgorithmVersion": result.planner_algorithm_version,
                "capabilityCatalogRevision": result.capability_catalog_revision,
                "entropyBudget": result.entropy_budget,
                "estimatedEntropy": result.estimated_entropy,
            }
        )

    def _estimate_blueprint_entropy(self, blueprint: ACGBlueprint) -> int:
        agents = {
            step.agent_name
            for step in blueprint.step_nodes()
            if step.agent_name
        }
        return max(0, len(agents) - 1) * self.cognitive_router.entropy_per_edge

    def _validate_agents(self, blueprint: ACGBlueprint, *, domain: str) -> None:
        missing: list[str] = []
        for step in blueprint.step_nodes():
            try:
                self.cognitive_router.agent_registry.resolve(
                    domain=domain,
                    agent_name=step.agent_name,
                    capability=step.capability,
                )
            except KeyError:
                missing.append(step.agent_name or step.node_id)
        if missing:
            raise ACGPlanningError("ACG references unregistered Agents: " + ", ".join(sorted(set(missing))))


__all__ = ["PlanningEngine", "PlanResult", "ACGPlanningError"]
