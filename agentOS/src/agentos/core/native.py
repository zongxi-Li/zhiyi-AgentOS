"""Core-owned bootstrap definition and deterministic native execution capability."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any

from agentos.adapters.model_adapter import StructuredGenerationError
from agentos.adapters.tool_adapter import network_tools_enabled
from agentos.agents.base import AgentOutput, AgentProfile, AgentRunContext, BaseAgent
from agentos.core.data_contracts import (
    ContextContractError,
    apply_contract_defaults,
    validate_contract_payload,
)
from agentos.core.models.types import WorkflowDefinition, WorkflowDefinitionType, utc_now
from agentos.core.native_prompt import (
    NATIVE_ARTIFACT_PROMPT_VERSION,
    NATIVE_CAPABILITY_PROMPT_VERSION,
    NativeCapabilityPromptBuilder,
)
from agentos.core.planning.native_capabilities import NATIVE_CAPABILITY_IDS
from agentos.core.recovery.contract_adapter import (
    normalize_payload_shape,
    prepare_contract_repair,
)
from agentos.core.tool_execution import execute_read_only_tool


NATIVE_ACG_WORKFLOW_ID = "native_acg_runtime_v1"
NATIVE_AGENT_NAME = "native_general_agent"
NATIVE_RECOVERY_CAPABILITIES = (
    "evidence_retrieval",
    "evidence_validation",
    "contract_adapter",
)
# Backward-compatible export derived from the native Catalog contribution.
NATIVE_CAPABILITIES = (*NATIVE_CAPABILITY_IDS, *NATIVE_RECOVERY_CAPABILITIES)


class ArtifactSemanticError(ValueError):
    """A schema-valid artifact is not a truthful, actionable deliverable."""

    def __init__(self, issues: list[str]):
        self.issues = list(dict.fromkeys(str(item) for item in issues if str(item)))
        super().__init__("; ".join(self.issues))


class NativeGeneralAgent(BaseAgent):
    """Small offline-safe Agent that executes the native bootstrap capabilities."""

    def __init__(
        self,
        *,
        agent_name: str = NATIVE_AGENT_NAME,
        binding_priority: int = 0,
    ) -> None:
        super().__init__(
            AgentProfile(
                agentName=agent_name,
                domain="general",
                capabilities=list(NATIVE_CAPABILITIES),
                bindingPriority=binding_priority,
                allowedTools=[
                    "web_search",
                    "knowledge_search",
                    "current_datetime",
                ],
                description="Executes domain-neutral understanding, analysis, and artifact delivery.",
            )
        )
        self.prompt_builder = NativeCapabilityPromptBuilder()
    async def run(self, context: AgentRunContext) -> AgentOutput:
        objective = str(
            context.task.input.get("userIntent")
            or context.task.input.get("intent")
            or context.task.title
        ).strip()
        upstream = self._upstream_data(context)
        capability = (context.step.capability or "").strip()

        task_summary = str(upstream.get("task_summary") or objective)
        if capability == "evidence_retrieval":
            web = None
            if network_tools_enabled(context.task.input):
                web = await execute_read_only_tool(
                    context.tool_runtime,
                    "web_search",
                    {"query": task_summary[:500], "max_results": 5, "topic": "general"},
                )
            if web is not None and web.ok and web.sources:
                refs = [
                    str(item.get("citationId"))
                    for item in web.sources
                    if item.get("citationId")
                ]
                information = [
                    str(item.get("snippet") or item.get("content") or "").strip()
                    for item in web.results
                    if str(item.get("snippet") or item.get("content") or "").strip()
                ]
                return AgentOutput(
                    output={
                        "recovered_information": information,
                        "recovered_sources": web.sources,
                        "recovered_evidence_refs": refs,
                        "recovery_mode": "web_search",
                    },
                    summary=f"Recovered {len(refs)} public web source(s).",
                    sources=web.sources,
                    toolExecutions=web.executions,
                    evidenceRefs=refs,
                )
            citation_id = "src_recovery_" + hashlib.sha256(
                f"{context.run.run_id}:{task_summary}".encode("utf-8")
            ).hexdigest()[:16]
            source = {
                "citationId": citation_id,
                "title": "Recovered user-provided task facts",
                "filename": None,
                "url": None,
                "content": task_summary[:4000],
                "provider": "task-input-recovery",
                "retrievedAt": utc_now().isoformat(),
                "provisional": True,
            }
            return AgentOutput(
                output={
                    "recovered_information": [task_summary],
                    "recovered_sources": [source],
                    "recovered_evidence_refs": [citation_id],
                    "recovery_mode": "task_input",
                },
                summary="Recovered task facts for evidence validation.",
                sources=[source],
                toolExecutions=web.executions if web is not None else [],
                evidenceRefs=[citation_id],
            )
        if capability == "evidence_validation":
            sources = list(upstream.get("recovered_sources") or [])
            refs = [
                str(value)
                for value in (upstream.get("recovered_evidence_refs") or [])
                if str(value)
            ]
            information = [
                str(value)
                for value in (upstream.get("recovered_information") or [])
                if str(value).strip()
            ]
            valid_refs = {
                str(item.get("citationId"))
                for item in sources
                if isinstance(item, dict) and item.get("citationId")
            }
            refs = [value for value in refs if value in valid_refs]
            return AgentOutput(
                output={
                    "validated_information": information,
                    "validated_sources": sources,
                    "validated_evidence_refs": refs,
                    "validation_status": "valid" if refs else "empty",
                },
                summary=f"Validated {len(refs)} recovered evidence source(s).",
                sources=sources,
                evidenceRefs=refs,
            )
        if capability == "contract_adapter":
            return AgentOutput(
                output=prepare_contract_repair(context),
                summary="Prepared the latest native payload for contract retry.",
            )
        if capability == "information_retrieval":
            validated_refs = list(upstream.get("validated_evidence_refs") or [])
            if validated_refs:
                validated_sources = list(upstream.get("validated_sources") or [])
                validated_information = list(upstream.get("validated_information") or [])
                return AgentOutput(
                    output={
                        "retrieved_information": validated_information,
                        "sources": validated_sources,
                        "evidence_refs": validated_refs,
                        "retrieval_mode": "recovered_task_input",
                        "runtimeSignals": [],
                    },
                    summary=f"Reused {len(validated_refs)} validated recovery source(s).",
                    sources=validated_sources,
                    evidenceRefs=validated_refs,
                )
            web = None
            if network_tools_enabled(context.task.input):
                web = await execute_read_only_tool(
                    context.tool_runtime,
                    "web_search",
                    {"query": task_summary[:500], "max_results": 5, "topic": "general"},
                )
            local = None
            if web is None or not web.ok or not web.sources:
                local = await execute_read_only_tool(
                    context.tool_runtime,
                    "knowledge_search",
                    {"query": task_summary[:500], "top_k": 5},
                )
            selected = (
                web
                if web is not None and web.ok and web.sources
                else local
                if local is not None and local.ok and local.sources
                else None
            )
            sources = list(selected.sources) if selected is not None else []
            evidence_refs = [
                str(item.get("citationId"))
                for item in sources
                if item.get("citationId")
            ]
            retrieved_information = [
                str(item.get("snippet") or item.get("content") or "").strip()
                for item in (selected.results if selected is not None else [])
                if str(item.get("snippet") or item.get("content") or "").strip()
            ]
            tool_executions = [
                execution
                for outcome in (web, local)
                if outcome is not None
                for execution in outcome.executions
            ]
            retrieval_errors = [
                {"tool": outcome.name, "error": outcome.error_code}
                for outcome in (web, local)
                if outcome is not None and outcome.error_code
            ]
            used_task_input_fallback = selected is None or not evidence_refs
            if used_task_input_fallback:
                citation_id = "src_task_input_" + hashlib.sha256(
                    task_summary.encode("utf-8")
                ).hexdigest()[:16]
                sources = [{
                    "citationId": citation_id,
                    "title": "User-provided task facts",
                    "filename": None,
                    "url": None,
                    "content": task_summary[:4000],
                    "provider": "task-input",
                    "retrievedAt": utc_now().isoformat(),
                }]
                evidence_refs = [citation_id]
                retrieved_information = [task_summary]
            output = {
                "retrieved_information": retrieved_information,
                "sources": sources,
                "evidence_refs": evidence_refs,
                "retrieval_mode": (
                    "web_search"
                    if selected is web and selected is not None
                    else "local_knowledge"
                    if selected is local and selected is not None
                    else "task_input_only"
                ),
                "retrieval_errors": retrieval_errors,
                "runtimeSignals": [],
            }
            if used_task_input_fallback and context.step.attempt <= 1:
                output["runtimeSignals"] = [
                    {
                        "type": "EVIDENCE_MISSING",
                        "code": "EVIDENCE_MISSING",
                        "targetNodeId": context.step.step_id,
                        "details": {
                            "requiredEvidenceTypes": ["retrievable_source"],
                            "fallbackMode": "task_input_only",
                        },
                    }
                ]
            return AgentOutput(
                output=output,
                summary=f"Prepared {len(evidence_refs)} evidence source(s).",
                sources=sources,
                toolExecutions=tool_executions,
                evidenceRefs=evidence_refs,
            )
        if capability == "evidence_analysis" and not upstream.get("evidence_refs"):
            raise RuntimeError("evidence_analysis requires upstream evidence references")

        descriptor = context.capability_descriptor
        if descriptor is None:
            raise StructuredGenerationError(
                "CAPABILITY_DESCRIPTOR_UNAVAILABLE",
                f"Capability descriptor is unavailable: {capability or '<empty>'}",
            )
        runtime = context.model_runtime
        if runtime is None or not runtime.is_available():
            raise StructuredGenerationError(
                "MODEL_UNAVAILABLE",
                "No production model is configured for native ACG execution.",
            )

        output_schema = dict(context.step.output_spec or descriptor.output_contract)
        generation_schema = self._generation_schema(capability, output_schema)
        pack = context.context_pack
        source_data = getattr(pack, "source_data", {}) if pack is not None else {}
        evidence_refs = list(getattr(pack, "evidence_refs", []) or []) if pack is not None else []
        prompt_method = (
            self.prompt_builder.build_artifact
            if capability == "artifact_generation"
            else self.prompt_builder.build
        )
        prompt = prompt_method(
            capability_descriptor=descriptor,
            step_goal=context.step.name,
            task_title=context.task.title,
            task_input=dict(context.task.input),
            context_data=upstream,
            source_data=dict(source_data) if isinstance(source_data, dict) else {},
            evidence_refs=evidence_refs,
            output_schema=generation_schema,
        )
        thinking_mode = (
            "disabled"
            if self.profile.agent_name == "native_general_fallback"
            else str(context.task.input.get("thinkingMode") or "disabled")
        )
        output_thinking_mode = thinking_mode
        timeout_seconds = 180.0 if capability == "artifact_generation" else 120.0
        max_output_tokens = 8192 if capability == "artifact_generation" else 4096
        prompt_version = (
            NATIVE_ARTIFACT_PROMPT_VERSION
            if capability == "artifact_generation"
            else NATIVE_CAPABILITY_PROMPT_VERSION
        )
        invocations: list[dict[str, Any]] = []
        repair_used = False
        thinking_fallback_reason: str | None = None
        try:
            generated = await runtime.generate_json(
                prompt=prompt,
                schema=generation_schema,
                thinking_mode=thinking_mode,
                timeout_seconds=timeout_seconds,
                max_output_tokens=max_output_tokens,
                prompt_version=prompt_version,
            )
        except StructuredGenerationError as exc:
            thinking_enabled = thinking_mode.strip().lower() not in {
                "",
                "disabled",
                "false",
                "none",
                "off",
            }
            if exc.code == "MODEL_EMPTY_RESPONSE":
                if thinking_enabled:
                    thinking_fallback_reason = exc.code
                output_thinking_mode = "disabled"
                generated = await runtime.generate_json(
                    prompt=self.prompt_builder.build_json_repair(
                        original_prompt=prompt,
                        validation_error=str(exc),
                    ),
                    schema=generation_schema,
                    thinking_mode=output_thinking_mode,
                    timeout_seconds=timeout_seconds,
                    max_output_tokens=max_output_tokens,
                    prompt_version=(
                        f"{prompt_version}.thinking-finalization1"
                        if thinking_enabled
                        else f"{prompt_version}.empty-response-retry1"
                    ),
                )
            elif exc.code != "MODEL_OUTPUT_INVALID_JSON":
                raise
            else:
                repair_used = True
                generated = await runtime.generate_json(
                    prompt=self.prompt_builder.build_json_repair(
                        original_prompt=prompt,
                        validation_error=str(exc),
                    ),
                    schema=generation_schema,
                    thinking_mode=output_thinking_mode,
                    timeout_seconds=timeout_seconds,
                    max_output_tokens=max_output_tokens,
                    prompt_version=f"{prompt_version}.json-repair1",
                )
        generation_audit = generated.audit_record()
        if thinking_fallback_reason:
            generation_audit["usage"].update(
                {
                    "thinkingFallback": True,
                    "thinkingFallbackReason": thinking_fallback_reason,
                    "requestedThinkingMode": thinking_mode,
                    "effectiveThinkingMode": output_thinking_mode,
                }
            )
        invocations.append(generation_audit)
        output = normalize_payload_shape(dict(generated.data), generation_schema)
        output = apply_contract_defaults(output, generation_schema)
        if capability == "artifact_generation":
            initial_error: Exception | None = None
            try:
                output = self._finalize_artifact_candidate(context, output)
                self._validate_artifact_output(context, output, output_schema)
            except (ContextContractError, ArtifactSemanticError) as exc:
                initial_error = exc

            if initial_error is not None:
                try:
                    repaired = await runtime.generate_json(
                        prompt=self.prompt_builder.build_repair(
                            original_prompt=prompt,
                            invalid_data=output,
                            validation_error=str(initial_error),
                        ),
                        schema=generation_schema,
                        thinking_mode=output_thinking_mode,
                        timeout_seconds=timeout_seconds,
                        max_output_tokens=max_output_tokens,
                        prompt_version=f"{prompt_version}.semantic-repair1",
                    )
                    invocations.append(repaired.audit_record())
                    output = normalize_payload_shape(
                        dict(repaired.data), generation_schema
                    )
                    output = apply_contract_defaults(output, generation_schema)
                    output = self._finalize_artifact_candidate(context, output)
                    self._validate_artifact_output(context, output, output_schema)
                    return AgentOutput(
                        output=output,
                        summary=(
                            "Native artifact completed after one semantic regeneration; "
                            f"initial validation: {initial_error}"
                        ),
                        modelInvocations=invocations,
                    )
                except (ContextContractError, ArtifactSemanticError, StructuredGenerationError) as repair_exc:
                    invocations.extend(
                        dict(item)
                        for item in (
                            getattr(repair_exc, "model_invocations", None) or []
                        )
                        if isinstance(item, dict)
                    )
                    output = self._build_degraded_artifact(
                        context,
                        reason=(
                            f"initial={initial_error}; repair={repair_exc}"
                        ),
                    )
                    self._validate_artifact_output(context, output, output_schema)
                    return AgentOutput(
                        output=output,
                        summary=(
                            "Native artifact used deterministic upstream aggregation "
                            "after semantic regeneration failed."
                        ),
                        modelInvocations=invocations,
                    )
            return AgentOutput(
                output=output,
                summary="Native artifact completed after semantic validation.",
                modelInvocations=invocations,
            )
        try:
            validate_contract_payload(
                output,
                output_schema,
                step_id=context.step.step_id,
                direction="output",
            )
        except ContextContractError as exc:
            if repair_used:
                raise StructuredGenerationError(
                    "OUTPUT_CONTRACT_VIOLATION",
                    str(exc),
                    direction="output",
                    partial_data=output,
                    model_invocations=invocations,
                ) from exc
            repair_used = True
            repaired = await runtime.generate_json(
                prompt=self.prompt_builder.build_repair(
                    original_prompt=prompt,
                    invalid_data=output,
                    validation_error=str(exc),
                ),
                schema=generation_schema,
                thinking_mode=output_thinking_mode,
                timeout_seconds=timeout_seconds,
                max_output_tokens=max_output_tokens,
                prompt_version=f"{prompt_version}.repair1",
            )
            invocations.append(repaired.audit_record())
            output = normalize_payload_shape(dict(repaired.data), generation_schema)
            output = apply_contract_defaults(output, generation_schema)
            try:
                validate_contract_payload(
                    output,
                    output_schema,
                    step_id=context.step.step_id,
                    direction="output",
                )
            except ContextContractError as repair_exc:
                raise StructuredGenerationError(
                    "OUTPUT_CONTRACT_VIOLATION",
                    str(repair_exc),
                    direction="output",
                    partial_data=output,
                    model_invocations=invocations,
                ) from repair_exc

        return AgentOutput(
            output=output,
            summary=f"Native capability completed: {capability}.",
            modelInvocations=invocations,
        )

    @staticmethod
    def _generation_schema(
        capability: str,
        output_schema: dict[str, Any],
    ) -> dict[str, Any]:
        """Return the semantic contract owned by the model.

        Runtime output remains governed by ``output_schema``.  Final Markdown and
        the Artifact envelope are deterministic projections, so asking the model
        to reproduce them would duplicate the deliverable and waste its bounded
        completion budget.
        """

        schema = deepcopy(output_schema)
        if capability != "artifact_generation":
            return schema
        properties = schema.get("properties")
        if not isinstance(properties, dict):
            return schema
        semantic_fields = {"deliverable", "verification"}
        schema["properties"] = {
            name: value
            for name, value in properties.items()
            if name in semantic_fields
        }
        schema["required"] = [
            name
            for name in schema.get("required", [])
            if name in semantic_fields
        ]
        return schema

    _ARTIFACT_INTERNAL_FIELDS = {
        "artifact",
        "final_answer",
        "runtimeSignals",
        "runtime_signals",
        "adapter_direction",
        "adapter_target_node_id",
        "adapter_source_event_id",
        "adapter_source_attempt_id",
        "adapter_status",
        "adapter_operations",
        "adapter_issues",
        "repair_kind",
        "original_payload_hash",
        "adapted_payload_hash",
        "adapted_payload",
    }
    _ARTIFACT_PLACEHOLDERS = {
        "unknown",
        "n/a",
        "na",
        "none",
        "null",
        "待补充",
        "未知",
    }
    _VERIFICATION_RANK = {"passed": 0, "partial": 1, "failed": 2}

    @staticmethod
    def _semantic_text(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )

    @classmethod
    def _is_substantive(cls, value: Any) -> bool:
        if value in (None, "", [], {}):
            return False
        text = cls._semantic_text(value)
        return bool(text) and text.lower() not in cls._ARTIFACT_PLACEHOLDERS

    @classmethod
    def _artifact_source_entries(
        cls,
        context: AgentRunContext,
    ) -> list[tuple[str, str, Any]]:
        pack = context.context_pack
        source_data = getattr(pack, "source_data", None) if pack is not None else None
        if not isinstance(source_data, dict) or not source_data:
            upstream = cls._upstream_data(context)
            source_data = {"upstream": upstream} if upstream else {}
        entries: list[tuple[str, str, Any]] = []
        for producer in sorted(source_data, key=str):
            fields = source_data.get(producer)
            if not isinstance(fields, dict):
                continue
            for field in sorted(fields, key=str):
                name = str(field)
                lowered = name.lower()
                if (
                    name.startswith("_")
                    or name in cls._ARTIFACT_INTERNAL_FIELDS
                    or any(
                        secret in lowered
                        for secret in ("password", "secret", "access_token", "api_key")
                    )
                ):
                    continue
                value = fields[field]
                if cls._is_substantive(value):
                    entries.append((str(producer), name, deepcopy(value)))
        return entries

    @staticmethod
    def _dedupe_strings(values: list[Any], *, max_length: int = 800) -> list[str]:
        result: list[str] = []
        for value in values:
            text = str(value or "").strip()
            if not text:
                continue
            text = text[:max_length]
            if text not in result:
                result.append(text)
        return result

    @classmethod
    def _criterion_texts(cls, value: Any) -> list[str]:
        if isinstance(value, str):
            return [value.strip()] if value.strip() else []
        if isinstance(value, list):
            return [
                item
                for nested in value
                for item in cls._criterion_texts(nested)
            ]
        if isinstance(value, dict):
            for key in (
                "criterion",
                "target",
                "name",
                "description",
                "requirement",
                "deliverable",
            ):
                if cls._is_substantive(value.get(key)):
                    return cls._criterion_texts(value[key])
            rendered = cls._semantic_text(value)
            return [rendered] if rendered else []
        if value not in (None, ""):
            return [str(value)]
        return []

    @classmethod
    def _requested_criteria(
        cls,
        context: AgentRunContext,
        entries: list[tuple[str, str, Any]],
    ) -> list[str]:
        values: list[Any] = [context.task.input.get("expectedArtifacts")]
        values.extend(
            value
            for _producer, field, value in entries
            if field in {"acceptance_criteria", "success_criteria"}
        )
        return cls._dedupe_strings(
            [item for value in values for item in cls._criterion_texts(value)],
            max_length=2000,
        )

    @classmethod
    def _upstream_verifications(
        cls,
        entries: list[tuple[str, str, Any]],
    ) -> list[dict[str, Any]]:
        return [
            deepcopy(value)
            for _producer, field, value in entries
            if field == "verification" and isinstance(value, dict)
        ]

    @classmethod
    def _finalize_artifact_candidate(
        cls,
        context: AgentRunContext,
        output: dict[str, Any],
        *,
        degraded: bool = False,
        extra_gaps: list[str] | None = None,
    ) -> dict[str, Any]:
        normalized = deepcopy(output)
        entries = cls._artifact_source_entries(context)
        deliverable = normalized.get("deliverable")
        if isinstance(deliverable, dict):
            refs = list(deliverable.get("sourceRefs") or [])
            pack = context.context_pack
            refs.extend(
                list(getattr(pack, "evidence_refs", []) or [])
                if pack is not None
                else []
            )
            for _producer, field, value in entries:
                if field in {"evidence_refs", "evidenceRefs", "sourceRefs"}:
                    refs.extend(value if isinstance(value, list) else [value])
            all_refs = cls._dedupe_strings(refs)
            deliverable["sourceRefs"] = all_refs[:12]
            normalized["deliverable"] = deliverable
        else:
            all_refs = []

        verification = normalized.get("verification")
        verification = deepcopy(verification) if isinstance(verification, dict) else {}
        checks = [
            deepcopy(item)
            for item in (verification.get("checks") or [])
            if isinstance(item, dict)
        ]
        gaps = list(
            verification.get("unresolvedGaps")
            or verification.get("unresolved_gaps")
            or []
        )
        statuses = [str(verification.get("status") or "partial").lower()]
        for upstream in cls._upstream_verifications(entries):
            statuses.append(str(upstream.get("status") or "partial").lower())
            checks.extend(
                deepcopy(item)
                for item in (upstream.get("checks") or [])
                if isinstance(item, dict)
            )
            gaps.extend(
                upstream.get("unresolvedGaps")
                or upstream.get("unresolved_gaps")
                or []
            )

        if len(all_refs) > 12:
            gaps.append(
                f"{len(all_refs) - 12} source reference(s) exceeded the artifact limit: "
                + ", ".join(all_refs[12:])
            )
        gaps.extend(extra_gaps or [])

        existing_criteria = [
            str(item.get("criterion") or "").strip().lower()
            for item in checks
            if isinstance(item, dict)
        ]
        for criterion in cls._requested_criteria(context, entries):
            normalized_criterion = criterion.lower()
            if any(
                normalized_criterion in existing or existing in normalized_criterion
                for existing in existing_criteria
                if existing
            ):
                continue
            if len(checks) < 12:
                checks.append(
                    {
                        "criterion": criterion,
                        "result": "待复核",
                        "evidence": "任务定义或上游验收条件",
                    }
                )
                existing_criteria.append(normalized_criterion)
            gaps.append(f"验收条件尚未被成果明确验证：{criterion}")

        unique_checks: list[dict[str, str]] = []
        for item in checks:
            check = {
                "criterion": cls._semantic_text(item.get("criterion"))[:2000],
                "result": cls._semantic_text(item.get("result"))[:2000],
                "evidence": cls._semantic_text(item.get("evidence"))[:2000],
            }
            if check not in unique_checks:
                unique_checks.append(check)
        if len(unique_checks) > 12:
            gaps.append(
                f"{len(unique_checks) - 12} verification check(s) exceeded the artifact limit."
            )
            unique_checks = unique_checks[:12]

        normalized_statuses = [
            value if value in cls._VERIFICATION_RANK else "partial"
            for value in statuses
        ]
        if degraded:
            normalized_statuses.append("partial")
        status = max(
            normalized_statuses,
            key=lambda value: cls._VERIFICATION_RANK[value],
        )
        gaps = cls._dedupe_strings(gaps)
        if len(gaps) > 12:
            omitted = gaps[11:]
            gaps = gaps[:11] + [
                f"另有 {len(omitted)} 个缺口因展示上限合并记录："
                + "；".join(omitted)[:700]
            ]
        checks_complete = bool(unique_checks) and all(
            all(cls._is_substantive(item.get(key)) for key in ("criterion", "result", "evidence"))
            for item in unique_checks
        )
        if status == "passed" and (not checks_complete or gaps or degraded):
            status = "partial"
            if not checks_complete:
                gaps = cls._dedupe_strings(
                    gaps + ["验收检查缺少可核对的条件、结果或证据。"]
                )[:12]
        normalized["verification"] = {
            "status": status,
            "checks": unique_checks,
            "unresolvedGaps": gaps,
        }
        return cls._normalize_artifact_output(context, normalized)

    @classmethod
    def _validate_artifact_output(
        cls,
        context: AgentRunContext,
        output: dict[str, Any],
        output_schema: dict[str, Any],
    ) -> None:
        validate_contract_payload(
            output,
            output_schema,
            step_id=context.step.step_id,
            direction="output",
        )
        issues: list[str] = []
        deliverable = output.get("deliverable")
        verification = output.get("verification")
        artifact = output.get("artifact")
        if not isinstance(deliverable, dict):
            issues.append("deliverable is missing")
            deliverable = {}
        for field in ("title", "executiveSummary"):
            if not cls._is_substantive(deliverable.get(field)):
                issues.append(f"deliverable.{field} is empty or a placeholder")
        sections = deliverable.get("sections")
        if not isinstance(sections, list) or not sections:
            issues.append("deliverable.sections has no substantive section")
            sections = []
        referenced_fields: set[str] = set()
        for index, section in enumerate(sections):
            if not isinstance(section, dict):
                issues.append(f"deliverable.sections[{index}] is not an object")
                continue
            for field in ("title", "content"):
                if not cls._is_substantive(section.get(field)):
                    issues.append(f"deliverable.sections[{index}].{field} is empty")
            source_fields = section.get("sourceFields")
            if not isinstance(source_fields, list) or not source_fields:
                issues.append(
                    f"deliverable.sections[{index}].sourceFields is empty"
                )
            referenced_fields.update(str(item) for item in source_fields or [])

        gaps = (
            list(verification.get("unresolvedGaps") or [])
            if isinstance(verification, dict)
            else []
        )
        gap_text = " ".join(str(item) for item in gaps)
        source_fields = {
            field for _producer, field, _value in cls._artifact_source_entries(context)
        }
        uncovered = sorted(
            field
            for field in source_fields
            if field not in referenced_fields and field not in gap_text
        )
        if uncovered:
            issues.append("uncovered upstream fields: " + ", ".join(uncovered))

        expected_refs = list(
            getattr(context.context_pack, "evidence_refs", []) or []
        ) if context.context_pack is not None else []
        delivered_refs = list(deliverable.get("sourceRefs") or [])
        missing_refs = [
            str(ref)
            for ref in expected_refs
            if str(ref) not in delivered_refs and str(ref) not in gap_text
        ]
        if missing_refs:
            issues.append("missing evidence references: " + ", ".join(missing_refs))

        if not isinstance(verification, dict):
            issues.append("verification is missing")
        else:
            checks = verification.get("checks") or []
            if verification.get("status") == "passed":
                if gaps:
                    issues.append("passed verification contains unresolved gaps")
                if not checks or any(
                    not isinstance(item, dict)
                    or any(
                        not cls._is_substantive(item.get(key))
                        for key in ("criterion", "result", "evidence")
                    )
                    for item in checks
                ):
                    issues.append("passed verification lacks evidence-backed checks")

        expected_markdown = cls._render_artifact_markdown(deliverable, verification)
        if output.get("final_answer") != expected_markdown:
            issues.append("final_answer is not the deterministic artifact projection")
        nonempty_lines = [
            line for line in str(output.get("final_answer") or "").splitlines() if line.strip()
        ]
        if len(nonempty_lines) <= 1:
            issues.append("final_answer contains only a title")
        if not isinstance(artifact, dict):
            issues.append("artifact envelope is missing")
        else:
            if artifact.get("content") != output.get("final_answer"):
                issues.append("artifact.content differs from final_answer")
            if artifact.get("structuredData") != deliverable:
                issues.append("artifact.structuredData differs from deliverable")
            if artifact.get("title") != deliverable.get("title"):
                issues.append("artifact.title differs from deliverable.title")
        if issues:
            raise ArtifactSemanticError(issues)

    @classmethod
    def _artifact_category(cls, field: str) -> str:
        lowered = field.lower()
        groups = (
            ("task", ("task", "requirement", "acceptance", "success", "constraint")),
            ("process", ("process", "resource", "capacity", "schedule", "timeline")),
            ("solution", ("architecture", "solution", "design", "implementation", "plan", "component", "data_flow")),
            ("evidence", ("evidence", "retrieved", "source", "citation")),
            ("comparison", ("compar", "alternative", "cost", "budget", "calculation")),
            ("risk", ("risk", "control", "mitigation")),
            ("verification", ("verification", "remediation", "gap", "question", "assumption")),
        )
        for category, tokens in groups:
            if any(token in lowered for token in tokens):
                return category
        return "analysis"

    @classmethod
    def _build_degraded_artifact(
        cls,
        context: AgentRunContext,
        *,
        reason: str,
    ) -> dict[str, Any]:
        entries = cls._artifact_source_entries(context)
        if not entries:
            raise StructuredGenerationError(
                "ARTIFACT_DELIVERY_INCOMPLETE",
                "No substantive upstream output is available for a truthful artifact.",
                direction="output",
            )

        chinese = any(
            "\u4e00" <= char <= "\u9fff" for char in context.task.title
        )
        labels = {
            "task": "任务理解与需求" if chinese else "Task and requirements",
            "process": "流程与资源" if chinese else "Process and resources",
            "solution": "架构与实施方案" if chinese else "Architecture and solution",
            "evidence": "资料与证据" if chinese else "Sources and evidence",
            "comparison": "比较与成本分析" if chinese else "Comparison and cost",
            "risk": "风险与控制措施" if chinese else "Risks and controls",
            "verification": "验证与待确认事项" if chinese else "Verification and open items",
            "analysis": "综合分析" if chinese else "General analysis",
        }
        categorized: dict[str, list[tuple[str, str, Any]]] = {
            key: [] for key in labels
        }
        for entry in entries:
            categorized[cls._artifact_category(entry[1])].append(entry)

        sections: list[dict[str, Any]] = []
        gaps: list[str] = [
            "成果模型输出未通过语义校验，已使用确定性上游汇总。",
            str(reason)[:700],
        ]
        for category in labels:
            items = categorized[category]
            chunk_lines: list[str] = []
            chunk_fields: list[str] = []
            chunk_index = 1

            def flush() -> None:
                nonlocal chunk_lines, chunk_fields, chunk_index
                if not chunk_lines:
                    return
                if len(sections) >= 12:
                    gaps.extend(
                        f"成果章节上限导致字段未展开：{field}"
                        for field in chunk_fields
                    )
                else:
                    suffix = f" {chunk_index}" if chunk_index > 1 else ""
                    sections.append(
                        {
                            "title": labels[category] + suffix,
                            "content": "\n".join(chunk_lines),
                            "sourceFields": list(dict.fromkeys(chunk_fields)),
                        }
                    )
                chunk_lines = []
                chunk_fields = []
                chunk_index += 1

            for producer, field, value in items:
                rendered = cls._semantic_text(value)
                if len(rendered) > 1400:
                    rendered = rendered[:1400] + "…"
                    gaps.append(f"字段内容因单节长度限制被截断：{producer}.{field}")
                line = f"- **{producer}.{field}**: {rendered}"
                projected_length = len("\n".join(chunk_lines + [line]))
                if chunk_lines and (
                    projected_length > 1900 or len(set(chunk_fields + [field])) > 12
                ):
                    flush()
                chunk_lines.append(line)
                chunk_fields.append(field)
            flush()

        if not sections:
            raise StructuredGenerationError(
                "ARTIFACT_DELIVERY_INCOMPLETE",
                "Substantive upstream output could not be projected into report sections.",
                direction="output",
            )

        calculations: list[dict[str, Any]] = []
        assumptions: list[Any] = []
        questions: list[Any] = []
        for _producer, field, value in entries:
            if field == "calculations" and isinstance(value, list):
                calculations.extend(
                    deepcopy(item)
                    for item in value
                    if isinstance(item, dict)
                    and all(
                        key in item
                        for key in ("name", "formula", "inputs", "result", "assumptions")
                    )
                )
            if field == "assumptions":
                assumptions.extend(value if isinstance(value, list) else [value])
            if field in {"openQuestions", "open_questions"}:
                questions.extend(value if isinstance(value, list) else [value])
        calculations = calculations[:12]
        assumptions = cls._dedupe_strings(assumptions)[:12]
        questions = cls._dedupe_strings(questions)[:12]
        if not questions:
            questions = ["请人工复核降级汇总及其未解决缺口。"]

        seed = {
            "deliverable": {
                "title": str(context.task.title or "Workflow deliverable").strip(),
                "executiveSummary": (
                    "成果生成已降级；以下内容是已完成上游节点的可审计汇总，"
                    "未解决事项仍需业务或专业人员复核。"
                    if chinese
                    else "Artifact generation degraded to an auditable aggregation of completed upstream results; unresolved items still require review."
                ),
                "sections": sections,
                "calculations": calculations,
                "assumptions": assumptions,
                "openQuestions": questions,
                "sourceRefs": [],
            },
            "verification": {
                "status": "partial",
                "checks": [
                    {
                        "criterion": "成果汇编完整性",
                        "result": "已降级汇编，需复核",
                        "evidence": "已完成上游节点输出",
                    }
                ],
                "unresolvedGaps": gaps,
            },
        }
        output = cls._finalize_artifact_candidate(
            context,
            seed,
            degraded=True,
            extra_gaps=gaps,
        )
        output["_llm"] = {
            "success": False,
            "source": "deterministic_upstream_aggregation",
            "degraded": True,
            "error": str(reason)[:700],
        }
        return output

    @classmethod
    def _normalize_artifact_output(
        cls,
        context: AgentRunContext,
        output: dict[str, Any],
    ) -> dict[str, Any]:
        normalized = dict(output)
        deliverable = normalized.get("deliverable")
        if not isinstance(deliverable, dict):
            deliverable = {
                "title": context.task.title,
                "executiveSummary": str(deliverable or ""),
                "sections": [],
                "calculations": [],
                "assumptions": [],
                "openQuestions": [],
                "sourceRefs": [],
            }
            normalized["deliverable"] = deliverable
        final_answer = cls._render_artifact_markdown(
            deliverable,
            normalized.get("verification"),
        )
        normalized["final_answer"] = final_answer
        artifact_id = "artifact_" + hashlib.sha256(
            f"{context.run.run_id}:{context.step.step_id}:{context.step.attempt}".encode(
                "utf-8"
            )
        ).hexdigest()[:16]
        normalized["artifact"] = {
            "artifactId": artifact_id,
            "type": "report",
            "title": str(deliverable.get("title") or context.task.title),
            "mediaType": "text/markdown",
            "content": final_answer,
            "structuredData": deliverable,
        }
        return normalized

    @staticmethod
    def _render_artifact_markdown(
        deliverable: dict[str, Any],
        verification: Any,
    ) -> str:
        """Render one user-facing artifact from the structured semantic result."""

        def text(value: Any) -> str:
            if value is None:
                return ""
            if isinstance(value, str):
                return value.strip()
            return json.dumps(value, ensure_ascii=False, separators=(",", ":"))

        title = text(deliverable.get("title")) or "Workflow deliverable"
        executive_summary = text(deliverable.get("executiveSummary"))
        language_sample = title + executive_summary
        chinese = any("\u4e00" <= character <= "\u9fff" for character in language_sample)
        labels = {
            "calculations": "计算与依据" if chinese else "Calculations and basis",
            "formula": "公式" if chinese else "Formula",
            "inputs": "输入" if chinese else "Inputs",
            "result": "结果" if chinese else "Result",
            "assumptions": "假设" if chinese else "Assumptions",
            "questions": "待确认事项" if chinese else "Open questions",
            "sources": "来源引用" if chinese else "Source references",
            "verification": "验收核对" if chinese else "Verification",
            "status": "状态" if chinese else "Status",
            "gaps": "未解决缺口" if chinese else "Unresolved gaps",
        }
        lines = [f"# {title}"]
        if executive_summary:
            lines.extend(["", executive_summary])

        for section in deliverable.get("sections") or []:
            if not isinstance(section, dict):
                continue
            section_title = text(section.get("title"))
            content = text(section.get("content"))
            if section_title:
                lines.extend(["", f"## {section_title}"])
            if content:
                lines.extend(["", content])

        calculations = deliverable.get("calculations") or []
        if calculations:
            lines.extend(["", f"## {labels['calculations']}"])
            for calculation in calculations:
                if not isinstance(calculation, dict):
                    continue
                name = text(calculation.get("name"))
                if name:
                    lines.extend(["", f"### {name}"])
                for key in ("formula", "inputs", "result", "assumptions"):
                    value = calculation.get(key)
                    if value in (None, "", []):
                        continue
                    rendered = ", ".join(text(item) for item in value) if isinstance(value, list) else text(value)
                    lines.append(f"- **{labels[key]}**: {rendered}")

        for key, label in (
            ("assumptions", labels["assumptions"]),
            ("openQuestions", labels["questions"]),
            ("sourceRefs", labels["sources"]),
        ):
            values = deliverable.get(key) or []
            if values:
                lines.extend(["", f"## {label}"])
                lines.extend(f"- {text(item)}" for item in values)

        if isinstance(verification, dict):
            lines.extend(["", f"## {labels['verification']}"])
            status = text(verification.get("status"))
            if status:
                lines.append(f"- **{labels['status']}**: {status}")
            for check in verification.get("checks") or []:
                if not isinstance(check, dict):
                    continue
                criterion = text(check.get("criterion"))
                result = text(check.get("result"))
                evidence = text(check.get("evidence"))
                rendered = " — ".join(item for item in (criterion, result, evidence) if item)
                if rendered:
                    lines.append(f"- {rendered}")
            gaps = verification.get("unresolvedGaps") or []
            if gaps:
                lines.append(f"- **{labels['gaps']}**: " + "; ".join(text(item) for item in gaps))

        return "\n".join(lines).strip()

    @staticmethod
    def _upstream_data(context: AgentRunContext) -> dict[str, Any]:
        pack = context.context_pack
        data = getattr(pack, "data", None) if pack is not None else None
        return dict(data) if isinstance(data, dict) else {}


class NativeGeneralFallbackAgent(NativeGeneralAgent):
    """Lower-priority compatible binding for transient primary failures."""

    def __init__(self) -> None:
        super().__init__(
            agent_name="native_general_fallback",
            binding_priority=-100,
        )

    async def run(self, context: AgentRunContext) -> AgentOutput:
        try:
            return await super().run(context)
        except StructuredGenerationError as exc:
            descriptor = context.capability_descriptor
            if descriptor is None:
                raise
            capability = str(context.step.capability or "").strip()
            output_schema = dict(context.step.output_spec or descriptor.output_contract)
            generation_schema = self._generation_schema(capability, output_schema)
            partial = dict(getattr(exc, "partial_data", None) or {})
            output = apply_contract_defaults(partial, generation_schema)
            if capability == "task_understanding" and not output.get("task_summary"):
                output["task_summary"] = str(
                    context.task.input.get("userIntent")
                    or context.task.input.get("intent")
                    or context.task.title
                ).strip()
            if capability == "verification":
                verification = output.get("verification")
                if isinstance(verification, dict):
                    verification["status"] = "partial"
                    verification.setdefault("unresolved_gaps", []).append(
                        "结构化模型输出不可用，需人工复核。"
                    )
            if capability == "artifact_generation":
                output = self._build_degraded_artifact(
                    context,
                    reason=f"{exc.code}: {exc}",
                )
                self._validate_artifact_output(context, output, output_schema)
            else:
                try:
                    validate_contract_payload(
                        output,
                        output_schema,
                        step_id=context.step.step_id,
                        direction="output",
                    )
                except ContextContractError:
                    raise exc
            output["_llm"] = {
                "success": False,
                "source": (
                    "deterministic_upstream_aggregation"
                    if capability == "artifact_generation"
                    else "explicit_schema_defaults"
                ),
                "error": f"{exc.code}: {exc}",
            }
            return AgentOutput(
                output=output,
                summary=f"Native fallback projected a valid contract for {capability}.",
                modelInvocations=list(getattr(exc, "model_invocations", None) or []),
            )


def native_bootstrap_definition() -> WorkflowDefinition:
    """Return the empty ACG definition that enters the existing PlanningEngine."""

    return WorkflowDefinition(
        workflowId=NATIVE_ACG_WORKFLOW_ID,
        name="知弈OS原生 ACG 运行时",
        domain="general",
        intent="general",
        runtimeEngine="acg",
        definitionType=WorkflowDefinitionType.NATIVE_BOOTSTRAP,
        description="Core-owned planner bootstrap for native domain-neutral tasks.",
        steps=[],
    )


def register_native_runtime(*, agent_registry, workflow_registry) -> None:
    """Register Core definitions before any application Pack is discovered."""

    agent_registry.register(NativeGeneralAgent())
    agent_registry.register(NativeGeneralFallbackAgent())
    workflow_registry.register(native_bootstrap_definition())


__all__ = [
    "NATIVE_ACG_WORKFLOW_ID",
    "NATIVE_AGENT_NAME",
    "NATIVE_CAPABILITIES",
    "NATIVE_RECOVERY_CAPABILITIES",
    "NativeGeneralAgent",
    "NativeGeneralFallbackAgent",
    "native_bootstrap_definition",
    "register_native_runtime",
]
