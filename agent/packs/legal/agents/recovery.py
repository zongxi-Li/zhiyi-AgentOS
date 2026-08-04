"""Legal recovery agents used by Core's domain-neutral ACG recipes."""

from __future__ import annotations

import hashlib
from typing import Any

from agentos.agents.base import AgentOutput, AgentProfile, BaseAgent
from agentos.core.recovery.contract_adapter import prepare_contract_repair
from app.rag.legal_evidence_schema import normalize_evidence


def _observation_values(context) -> list[dict[str, Any]]:
    return [
        value
        for value in context.memory.observations.values()
        if isinstance(value, dict)
    ]


def _latest_field(context, field: str) -> Any:
    for value in reversed(_observation_values(context)):
        if field in value:
            return value[field]
    return None


class LegalEvidenceRecoveryAgent(BaseAgent):
    """Preserve unmatched risks as low-confidence, provenance-marked task facts."""

    def __init__(self) -> None:
        super().__init__(
            AgentProfile(
                agentName="legal_evidence_recovery",
                domain="legal",
                capabilities=["evidence_retrieval"],
                description="Recovers missing legal evidence as provenance-marked task facts.",
            )
        )

    async def run(self, context) -> AgentOutput:
        observations = _observation_values(context)
        risk_output = next(
            (item for item in reversed(observations) if isinstance(item.get("risks"), list)),
            {},
        )
        match_output = next(
            (item for item in reversed(observations) if isinstance(item.get("retrieval"), dict)),
            {},
        )
        unmatched = {
            str(value)
            for value in (match_output.get("retrieval", {}).get("unmatched_risk_ids") or [])
            if str(value)
        }
        risks = [
            item
            for item in (risk_output.get("risks") or [])
            if isinstance(item, dict) and (not unmatched or str(item.get("id") or "") in unmatched)
        ]
        contract_text = str(
            context.task.input.get("contractText")
            or context.task.input.get("caseText")
            or context.task.input.get("text")
            or context.task.input.get("userIntent")
            or context.task.title
        ).strip()
        recovered: list[dict[str, Any]] = []
        for index, risk in enumerate(risks, start=1):
            risk_id = str(risk.get("id") or f"risk-{index:02d}")
            digest = hashlib.sha256(
                f"{context.run.run_id}:{risk_id}:task-fact".encode("utf-8")
            ).hexdigest()[:12]
            recovered.append(
                normalize_evidence(
                    {
                        "id": f"recovered-{digest}",
                        "riskId": risk_id,
                        "stepId": context.step.step_id,
                        "sourceType": "task-input",
                        "sourceName": "User-provided contract facts",
                        "title": str(risk.get("title") or "Unmatched contract risk"),
                        "content": contract_text[:2000],
                        "citationText": "用户提供的合同事实；尚待权威法律依据复核",
                        "confidence": 0.25,
                        "retrievalScore": 0.0,
                        "metadata": {
                            "provisional": True,
                            "authoritativeSourceMissing": True,
                        },
                    },
                    risk_id=risk_id,
                )
            )
        return AgentOutput(
            output={
                "recovered_evidences": recovered,
                "recovery_status": "recovered" if recovered else "nothing_to_recover",
            },
            summary=f"Recovered {len(recovered)} provenance-marked legal evidence item(s).",
        )


class LegalEvidenceValidationAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            AgentProfile(
                agentName="legal_evidence_validation",
                domain="legal",
                capabilities=["evidence_validation"],
                description="Validates and deduplicates recovered legal evidence.",
            )
        )

    async def run(self, context) -> AgentOutput:
        candidates = _latest_field(context, "recovered_evidences") or []
        validated: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        for item in candidates:
            if not isinstance(item, dict):
                continue
            normalized = normalize_evidence(item)
            key = (normalized["riskId"], normalized["id"])
            if not normalized["riskId"] or not normalized["content"] or key in seen:
                continue
            seen.add(key)
            validated.append(normalized)
        return AgentOutput(
            output={
                "validated_evidences": validated,
                "validation_status": "valid" if validated else "empty",
            },
            summary=f"Validated {len(validated)} recovered legal evidence item(s).",
        )


class LegalContractAdapterAgent(BaseAgent):
    """Expose the Core contract-repair capability for the legal domain."""

    def __init__(self) -> None:
        super().__init__(
            AgentProfile(
                agentName="legal_contract_adapter",
                domain="legal",
                capabilities=["contract_adapter"],
                description="Normalizes the latest legal step payload for a bounded retry.",
            )
        )

    async def run(self, context) -> AgentOutput:
        repair = prepare_contract_repair(context)
        return AgentOutput(
            output=repair,
            summary="Prepared the latest legal payload for contract retry.",
        )


__all__ = [
    "LegalContractAdapterAgent",
    "LegalEvidenceRecoveryAgent",
    "LegalEvidenceValidationAgent",
]
