from __future__ import annotations

from typing import Any, Dict, List

from agentos.core.models.types import StepStatus, TraceEventType
from app.rag import LegalEvidenceRetriever
from app.rag.legal_evidence_schema import normalize_evidence
from app.graphs.contract_review.artifacts import LEGAL_EVIDENCE_MATCH, _artifacts, write_artifact
from app.graphs.contract_review.mock_data import (
    _evidence_items,
    _evidence_trace_payload,
    _fallback_evidence_for_risk,
)
from app.graphs.contract_review.nodes.common import _append_trace, _copy_state, _set_step
from app.graphs.contract_review.state import ContractReviewState


def legal_evidence_match_node(state: ContractReviewState) -> ContractReviewState:
    state = _copy_state(state)
    risks = state.get("risks", [])
    contract_type = str(_artifacts(state).get("parse_contract", {}).get("contract_type") or "")
    top_k = 2
    fallback = False
    error = None
    evidences: List[Dict[str, Any]] = []
    try:
        retriever = LegalEvidenceRetriever()
        for index, risk in enumerate(risks, start=1):
            results = retriever.retrieve(risk=risk, contract_type=contract_type, top_k=top_k)
            if results:
                evidences.extend(results)
            else:
                fallback = True
                evidences.append(_fallback_evidence_for_risk(risk, index))
        if not evidences:
            fallback = True
            evidences = _evidence_items()
    except Exception as exc:
        fallback = True
        error = str(exc)
        evidences = [_fallback_evidence_for_risk(risk, index) for index, risk in enumerate(risks, start=1)] or _evidence_items()

    evidences = [normalize_evidence(item, risk_id=str(item.get("riskId") or "")) for item in evidences]
    output = {
        "evidences": evidences,
        "citations": [item["citationText"] for item in evidences],
    }
    state["evidences"] = evidences
    write_artifact(state, LEGAL_EVIDENCE_MATCH, output)
    _set_step(state, "legal_evidence_match", StepStatus.COMPLETED.value, output)
    _append_trace(
        state,
        step_id="legal_evidence_match",
        event_type=TraceEventType.AGENT_CALLED.value,
        observation="Matched legal evidence to risks.",
        payload=_evidence_trace_payload(
            result_count=len(evidences),
            fallback=fallback,
            error=error,
            top_k=top_k,
            evidences=evidences,
        ),
    )
    return state
