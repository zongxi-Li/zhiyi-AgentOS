"""Lower-priority compatible binding for the canonical legal workflow."""

from __future__ import annotations

from agentos.agents.base import AgentProfile, BaseAgent
from packs.legal.agents.contract_review_migration import (
    ClauseClassifyAgent,
    ContractParseAgent,
    HumanReviewGateAgent,
    LegalEvidenceMatchAgent,
    ReportGenerateAgent,
    RevisionSuggestAgent,
    RiskDetectAgent,
)


class LegalWorkflowFallbackAgent(BaseAgent):
    """Route a retried legal step through a fresh, lower-priority agent binding."""

    def __init__(self) -> None:
        self._delegates = {
            "contract_parse": ContractParseAgent(),
            "clause_classify": ClauseClassifyAgent(),
            "risk_detect": RiskDetectAgent(),
            "legal_evidence_match": LegalEvidenceMatchAgent(),
            "revision_suggest": RevisionSuggestAgent(),
            "human_review_gate": HumanReviewGateAgent(),
            "report_generate": ReportGenerateAgent(),
        }
        super().__init__(
            AgentProfile(
                agentName="legal_workflow_fallback",
                domain="legal",
                capabilities=list(self._delegates),
                bindingPriority=-100,
                description="Fallback binding for canonical legal contract-review steps.",
            )
        )

    async def run(self, context):
        capability = str(context.step.capability or "")
        delegate = self._delegates.get(capability)
        if delegate is None:
            raise KeyError(f"unsupported legal fallback capability: {capability}")
        return await delegate.run(context)


__all__ = ["LegalWorkflowFallbackAgent"]
