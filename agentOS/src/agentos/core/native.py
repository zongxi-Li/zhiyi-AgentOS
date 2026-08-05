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
    NATIVE_CAPABILITY_PROMPT_VERSION,
    NativeCapabilityPromptBuilder,
)
from agentos.core.planning.native_capabilities import NATIVE_CAPABILITY_IDS
from agentos.core.recovery.contract_adapter import (
    normalize_payload_shape,
    prepare_contract_repair,
    repair_payload,
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
                prompt_version=NATIVE_CAPABILITY_PROMPT_VERSION,
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
                        f"{NATIVE_CAPABILITY_PROMPT_VERSION}.thinking-finalization1"
                        if thinking_enabled
                        else f"{NATIVE_CAPABILITY_PROMPT_VERSION}.empty-response-retry1"
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
                    prompt_version=f"{NATIVE_CAPABILITY_PROMPT_VERSION}.json-repair1",
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
            output = self._normalize_artifact_output(context, output)
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
                prompt_version=f"{NATIVE_CAPABILITY_PROMPT_VERSION}.repair1",
            )
            invocations.append(repaired.audit_record())
            output = normalize_payload_shape(dict(repaired.data), generation_schema)
            output = apply_contract_defaults(output, generation_schema)
            if capability == "artifact_generation":
                output = self._normalize_artifact_output(context, output)
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
            output = repair_payload(partial, generation_schema)
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
                output = self._fallback_artifact_seed(context, output)
                output = self._normalize_artifact_output(context, output)
            validate_contract_payload(
                output,
                output_schema,
                step_id=context.step.step_id,
                direction="output",
            )
            output["_llm"] = {
                "success": False,
                "source": "schema_projection",
                "error": f"{exc.code}: {exc}",
            }
            return AgentOutput(
                output=output,
                summary=f"Native fallback projected a valid contract for {capability}.",
                modelInvocations=list(getattr(exc, "model_invocations", None) or []),
            )

    @classmethod
    def _fallback_artifact_seed(
        cls,
        context: AgentRunContext,
        output: dict[str, Any],
    ) -> dict[str, Any]:
        normalized = dict(output)
        upstream = cls._upstream_data(context)
        deliverable = normalized.get("deliverable")
        if not isinstance(deliverable, dict):
            deliverable = {}
        sections = deliverable.get("sections")
        if not isinstance(sections, list) or not sections:
            sections = [
                {
                    "title": str(key).replace("_", " ").strip().title(),
                    "content": (
                        value.strip()
                        if isinstance(value, str)
                        else json.dumps(value, ensure_ascii=False, default=str)
                    )[:2000],
                    "sourceFields": [str(key)],
                }
                for key, value in list(upstream.items())[:8]
                if value not in (None, "", [], {})
            ]
        deliverable.update(
            {
                "title": str(deliverable.get("title") or context.task.title),
                "executiveSummary": str(
                    deliverable.get("executiveSummary")
                    or "模型结构化输出不可用；以下内容由已完成节点的可审计结果轻量汇总。"
                ),
                "sections": sections,
                "calculations": list(deliverable.get("calculations") or []),
                "assumptions": list(deliverable.get("assumptions") or []),
                "openQuestions": list(deliverable.get("openQuestions") or [])
                or ["请人工复核降级汇总结果。"],
                "sourceRefs": list(deliverable.get("sourceRefs") or []),
            }
        )
        normalized["deliverable"] = deliverable
        verification = normalized.get("verification")
        if not isinstance(verification, dict):
            verification = {}
        verification.update(
            {
                "status": "partial",
                "checks": list(verification.get("checks") or []),
                "unresolvedGaps": list(verification.get("unresolvedGaps") or [])
                or ["结构化模型输出不可用，已使用轻量汇总。"],
            }
        )
        normalized["verification"] = verification
        return normalized


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
