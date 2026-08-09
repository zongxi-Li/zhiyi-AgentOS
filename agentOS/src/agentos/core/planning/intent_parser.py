"""Catalog-driven parsing of bounded task context into a semantic profile."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Literal, Optional, Protocol

from agentos.core.acg.enums import ComplexityLevel
from agentos.core.planning.capabilities import (
    CapabilityCatalog,
    highest_planning_risk_level,
)
from agentos.core.planning.context import PlanningRequestContext
from agentos.core.planning.default_catalog import build_default_capability_catalog
from agentos.core.planning.profile import CapabilityCandidate, TaskSemanticProfile


class IntentLLM(Protocol):
    def generate_json(self, prompt: str, schema: Dict[str, Any], **kwargs) -> Dict[str, Any]: ...


IntentParseSource = Literal["llm", "heuristic"]
IntentFallbackReason = Literal[
    "llm_unavailable",
    "llm_timeout",
    "llm_invalid_response",
    "llm_no_registered_capability",
]


@dataclass(frozen=True)
class IntentParseOutcome:
    profile: TaskSemanticProfile
    source: IntentParseSource
    fallback_reason: IntentFallbackReason | None = None
    rejected_capabilities: tuple[str, ...] = ()
    llm_metadata: dict[str, Any] = field(default_factory=dict)


class _NoRegisteredCapability(ValueError):
    def __init__(self, rejected_capabilities: list[str]) -> None:
        super().__init__("LLM returned no executable registered capability")
        self.rejected_capabilities = rejected_capabilities


_PROFILE_SCHEMA = {
    "type": "object",
    "properties": {
        "primaryGoal": {"type": "string"},
        "keyConstraints": {"type": "array", "items": {"type": "string"}},
        "requiredCapabilities": {"type": "array", "items": {"type": "string"}},
        "expectedArtifacts": {"type": "array", "items": {"type": "string"}},
        "verificationRequirements": {"type": "array", "items": {"type": "string"}},
        "estimatedComplexity": {
            "type": "string",
            "enum": ["simple", "medium", "complex", "extreme"],
        },
        "domainHint": {"type": "string"},
        "taskTypeHint": {"type": "string"},
        "implicitRequirements": {"type": "array", "items": {"type": "string"}},
        "riskLevel": {"type": "string"},
    },
    "required": ["primaryGoal", "requiredCapabilities", "estimatedComplexity"],
}

_NATIVE_FALLBACK = ["task_understanding", "analysis", "artifact_generation"]
INTENT_PROMPT_VERSION = "intent-profile.v2"


class IntentParser:
    """Select registered capabilities with an auditable LLM-first fallback."""

    def __init__(
        self,
        llm: Optional[IntentLLM] = None,
        capability_catalog: CapabilityCatalog | None = None,
    ) -> None:
        self.llm = llm
        self.capability_catalog = capability_catalog or build_default_capability_catalog()

    def parse(
        self,
        *,
        intent: str,
        domain: str = "general",
        task_type: str = "general",
        thinking_mode: str | None = None,
        use_llm: bool = True,
        context: PlanningRequestContext | None = None,
    ) -> TaskSemanticProfile:
        """Compatibility wrapper returning only the semantic profile."""

        return self.parse_outcome(
            intent=intent,
            domain=domain,
            task_type=task_type,
            thinking_mode=thinking_mode,
            use_llm=use_llm,
            context=context,
        ).profile

    def parse_outcome(
        self,
        *,
        intent: str,
        domain: str = "general",
        task_type: str = "general",
        thinking_mode: str | None = None,
        use_llm: bool = True,
        context: PlanningRequestContext | None = None,
    ) -> IntentParseOutcome:
        planning_context = context or PlanningRequestContext(
            intent=intent,
            domain=domain,
            task_type=task_type,
        )
        if use_llm and self.llm is not None:
            try:
                profile, rejected, metadata = self._parse_with_llm(
                    planning_context,
                    thinking_mode,
                )
                return IntentParseOutcome(
                    profile=profile,
                    source="llm",
                    rejected_capabilities=tuple(rejected),
                    llm_metadata=metadata,
                )
            except _NoRegisteredCapability as exc:
                reason: IntentFallbackReason = "llm_no_registered_capability"
                fallback_rejected = tuple(exc.rejected_capabilities)
            except Exception as exc:
                message = str(exc).lower()
                reason = (
                    "llm_timeout"
                    if isinstance(exc, TimeoutError)
                    or any(
                        marker in message
                        for marker in ("timeout", "timed out", "deadline exceeded")
                    )
                    else "llm_invalid_response"
                )
                fallback_rejected = ()
        elif use_llm:
            reason = "llm_unavailable"
            fallback_rejected = ()
        else:
            reason = None
            fallback_rejected = ()
        return IntentParseOutcome(
            profile=self._heuristic(planning_context),
            source="heuristic",
            fallback_reason=reason,
            rejected_capabilities=fallback_rejected,
        )

    def _parse_with_llm(
        self,
        context: PlanningRequestContext,
        thinking_mode: str | None,
    ) -> tuple[TaskSemanticProfile, list[str], dict[str, Any]]:
        result = self.llm.generate_json(
            self.build_prompt(context=context),
            _PROFILE_SCHEMA,
            thinking_mode=thinking_mode,
            temperature=0.0,
            timeout=30.0,
        )
        data = result.get("data", result) if isinstance(result, dict) else {}
        data = dict(data) if isinstance(data, dict) else {}
        data.pop("entropyBudget", None)
        data.pop("entropy_budget", None)
        data.setdefault("domainHint", context.domain)
        data.setdefault("taskTypeHint", context.task_type)
        data["rawIntent"] = context.intent
        raw_capabilities = data.get("requiredCapabilities") or []
        normalized, rejected = self._normalize_capabilities_with_rejected(
            raw_capabilities,
            domain=context.domain,
        )
        if not normalized:
            raise _NoRegisteredCapability(rejected)
        data["requiredCapabilities"] = normalized
        data["keyConstraints"] = self._merge_authoritative(
            context.constraints,
            data.get("keyConstraints"),
        )
        data["expectedArtifacts"] = self._merge_authoritative(
            context.expected_artifacts,
            data.get("expectedArtifacts"),
        )
        data["verificationRequirements"] = self._merge_authoritative(
            context.verification_requirements,
            data.get("verificationRequirements"),
        )
        data["capabilityCandidates"] = [
            CapabilityCandidate(
                capabilityId=capability_id,
                score=1.0,
                matchedTerms=[],
                source="llm",
            ).model_dump(by_alias=True)
            for capability_id in normalized
        ]
        profile = TaskSemanticProfile.model_validate(data)
        if not profile.primary_goal.strip():
            raise ValueError("LLM returned no primary goal")
        metadata = {
            key: result.get(key)
            for key in ("provider", "model", "latency_ms")
            if isinstance(result, dict) and result.get(key) is not None
        }
        return self._finalize(profile, context=context), rejected, metadata

    def build_prompt(
        self,
        *,
        intent: str | None = None,
        domain: str = "general",
        task_type: str = "general",
        context: PlanningRequestContext | None = None,
    ) -> str:
        planning_context = context or PlanningRequestContext(
            intent=intent or "",
            domain=domain,
            task_type=task_type,
        )
        options = "\n".join(
            f"- {item.capability_id}: {item.display_name}；{item.description}"
            for item in self.capability_catalog.available(planning_context.domain)
        )
        sections = [
            f"规划提示版本：{INTENT_PROMPT_VERSION}",
            "你是任务规划的意图解析器。只返回 JSON。",
            "从下列目录选择实际需要执行的稳定 capabilityId，不得创造目录外能力。",
            f"可选执行能力：\n{options}",
            (
                "返回 primaryGoal、keyConstraints、requiredCapabilities、expectedArtifacts、"
                "verificationRequirements、estimatedComplexity、domainHint、taskTypeHint、"
                "implicitRequirements、riskLevel。"
            ),
            f"领域提示：{planning_context.domain}",
            f"任务类型提示：{planning_context.task_type}",
            f"用户目标：{planning_context.intent}",
        ]
        if planning_context.constraints:
            sections.append("显式约束（必须保留）：" + "；".join(planning_context.constraints))
        if planning_context.expected_artifacts:
            sections.append(
                "显式交付物（必须保留）：" + "；".join(planning_context.expected_artifacts)
            )
        if planning_context.verification_requirements:
            sections.append(
                "显式验证要求（必须保留）："
                + "；".join(planning_context.verification_requirements)
            )
        if planning_context.material.excerpt:
            sections.append("任务材料（仅用于识别所需能力）：\n" + planning_context.material.excerpt)
        return "\n\n".join(sections) + "\n"

    def _heuristic(self, context: PlanningRequestContext) -> TaskSemanticProfile:
        text = context.searchable_text
        length = len(text)
        complexity = (
            ComplexityLevel.EXTREME
            if length > 4000
            else ComplexityLevel.COMPLEX
            if length > 1200
            else ComplexityLevel.MEDIUM
            if length > 400
            else ComplexityLevel.SIMPLE
        )
        candidates = self._infer_capability_candidates(text, context.domain)
        capabilities = [candidate.capability_id for candidate in candidates]
        profile = TaskSemanticProfile(
            primaryGoal=context.intent[:80] or context.task_type,
            keyConstraints=list(context.constraints),
            requiredCapabilities=capabilities,
            capabilityCandidates=candidates,
            expectedArtifacts=list(context.expected_artifacts),
            verificationRequirements=list(context.verification_requirements),
            estimatedComplexity=complexity,
            domainHint=context.domain,
            taskTypeHint=context.task_type,
            riskLevel="normal",
            rawIntent=context.intent,
        )
        return self._finalize(profile, context=context)

    def _finalize(
        self,
        profile: TaskSemanticProfile,
        *,
        context: PlanningRequestContext,
    ) -> TaskSemanticProfile:
        normalized = self._normalize_capabilities(
            profile.required_capabilities,
            domain=context.domain,
        )
        if not normalized:
            normalized = []
            for capability_id in _NATIVE_FALLBACK:
                try:
                    self.capability_catalog.get(capability_id)
                except KeyError:
                    continue
                normalized.append(capability_id)
        profile.key_constraints = self._merge_authoritative(
            context.constraints,
            profile.key_constraints,
        )
        profile.expected_artifacts = self._merge_authoritative(
            context.expected_artifacts,
            profile.expected_artifacts,
        )
        profile.verification_requirements = self._merge_authoritative(
            context.verification_requirements,
            profile.verification_requirements,
        )
        normalized = self._ensure_semantic_capabilities(
            normalized,
            domain=context.domain,
            expected_artifacts=profile.expected_artifacts,
            verification_requirements=profile.verification_requirements,
        )
        explicit_capabilities = set(normalized)
        profile.required_capabilities = self.capability_catalog.expand_dependencies(normalized)
        by_capability = {
            candidate.capability_id: candidate for candidate in profile.capability_candidates
        }
        profile.capability_candidates = [
            by_capability.get(capability_id)
            or CapabilityCandidate(
                capabilityId=capability_id,
                score=1.0,
                matchedTerms=[],
                source=(
                    "dependency"
                    if capability_id not in explicit_capabilities
                    else "fallback"
                ),
            )
            for capability_id in profile.required_capabilities
        ]
        profile.risk_level = highest_planning_risk_level(
            [
                profile.risk_level,
                *(
                    self.capability_catalog.get(capability).risk_level_hint
                    for capability in profile.required_capabilities
                ),
            ]
        )
        profile.primary_goal = profile.primary_goal.strip() or (
            context.intent or context.task_type or "Unnamed task"
        )[:80]
        profile.domain_hint = context.domain
        profile.task_type_hint = context.task_type
        profile.raw_intent = context.intent
        return profile

    def _ensure_semantic_capabilities(
        self,
        capabilities: list[str],
        *,
        domain: str,
        expected_artifacts: list[str],
        verification_requirements: list[str],
    ) -> list[str]:
        selected = list(capabilities)
        descriptors = [self.capability_catalog.get(item) for item in selected]
        available = list(self.capability_catalog.available(domain))
        if expected_artifacts and not any(item.produces_artifact for item in descriptors):
            artifact_options = [item for item in available if item.produces_artifact]
            artifact_options.sort(
                key=lambda item: (
                    item.planning_stage not in {"deliver", "report"},
                    item.priority,
                    item.capability_id,
                )
            )
            if artifact_options:
                selected.append(artifact_options[0].capability_id)
        if verification_requirements and not any(
            item.planning_stage == "verify" for item in descriptors
        ):
            verification = next(
                (item for item in available if item.planning_stage == "verify"),
                None,
            )
            if verification is not None:
                selected.append(verification.capability_id)
        return list(dict.fromkeys(selected))

    def _infer_capabilities(self, text: str, domain: str) -> list[str]:
        return [
            candidate.capability_id
            for candidate in self._infer_capability_candidates(text, domain)
        ]

    def _infer_capability_candidates(
        self, text: str, domain: str
    ) -> list[CapabilityCandidate]:
        normalized_text = "".join(text.lower().split())
        matches: list[CapabilityCandidate] = []
        for descriptor in self.capability_catalog.available(domain):
            searchable_terms = list(
                dict.fromkeys(
                    [descriptor.capability_id, descriptor.display_name, *descriptor.aliases]
                )
            )
            matched_terms = [
                term
                for term in searchable_terms
                if (term_normalized := "".join(term.lower().split()))
                and term_normalized in normalized_text
            ]
            if matched_terms:
                longest = max(len("".join(term.split())) for term in matched_terms)
                score = min(1.0, 0.6 + 0.08 * len(matched_terms) + longest / 200)
                matches.append(
                    CapabilityCandidate(
                        capabilityId=descriptor.capability_id,
                        score=round(score, 4),
                        matchedTerms=matched_terms,
                        source="catalog_alias",
                    )
                )

        if domain.strip().lower() == "general":
            specialized = [
                item for item in matches if item.capability_id not in _NATIVE_FALLBACK
            ]
            if not specialized:
                return [
                    CapabilityCandidate(
                        capabilityId=capability_id,
                        score=1.0,
                        matchedTerms=[],
                        source="fallback",
                    )
                    for capability_id in _NATIVE_FALLBACK
                ]
            matches = [
                CapabilityCandidate(
                    capabilityId="task_understanding",
                    score=1.0,
                    matchedTerms=[],
                    source="fallback",
                ),
                *specialized,
            ]
            if "artifact_generation" not in {
                item.capability_id for item in matches
            }:
                matches.append(
                    CapabilityCandidate(
                        capabilityId="artifact_generation",
                        score=1.0,
                        matchedTerms=[],
                        source="fallback",
                    )
                )
        normalized = self._normalize_capabilities(
            [item.capability_id for item in matches],
            domain=domain,
        )
        by_capability = {item.capability_id: item for item in matches}
        return [by_capability[item] for item in normalized]

    def _normalize_capabilities(self, values, *, domain: str) -> list[str]:
        normalized, _ = self._normalize_capabilities_with_rejected(values, domain=domain)
        return normalized

    def _normalize_capabilities_with_rejected(
        self,
        values,
        *,
        domain: str,
    ) -> tuple[list[str], list[str]]:
        available = {
            descriptor.capability_id
            for descriptor in self.capability_catalog.available(domain)
        }
        normalized: list[str] = []
        rejected: list[str] = []
        for value in values if isinstance(values, (list, tuple, set)) else []:
            raw = str(value or "").strip()
            if not raw:
                continue
            try:
                descriptor = self.capability_catalog.resolve(raw)
            except KeyError:
                rejected.append(raw)
                continue
            if descriptor.capability_id not in available:
                rejected.append(raw)
            elif descriptor.capability_id not in normalized:
                normalized.append(descriptor.capability_id)
        return normalized, list(dict.fromkeys(rejected))

    @staticmethod
    def _merge_authoritative(authoritative, inferred) -> list[str]:
        values: list[str] = []
        for source in (authoritative, inferred):
            if isinstance(source, str):
                items = [source]
            elif isinstance(source, (list, tuple, set)):
                items = source
            else:
                items = []
            values.extend(str(item).strip() for item in items if str(item).strip())
        return list(dict.fromkeys(values))


__all__ = [
    "IntentFallbackReason",
    "IntentLLM",
    "IntentParseOutcome",
    "IntentParseSource",
    "IntentParser",
    "INTENT_PROMPT_VERSION",
    "TaskSemanticProfile",
]
