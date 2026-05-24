from __future__ import annotations

from app.graphs.contract_review import (
    ContractReviewState,
    LegalContractReviewStateGraphRuntime,
    WORKFLOW_ID,
    build_contract_review_graph,
)
from app.graphs.contract_review.artifacts import (
    ARTIFACT_PATHS,
    _artifacts,
    read_artifact,
    write_artifact,
)
from app.graphs.contract_review.mock_data import (
    _append_evidence_appendix,
    _evidence_items,
    _evidence_trace_payload,
    _fallback_evidence_for_risk,
    _mock_parse_contract_output,
    _risk_items,
)
from app.graphs.contract_review.nodes.classify_clauses import classify_clauses_node
from app.graphs.contract_review.nodes.human_review import human_review_node
from app.graphs.contract_review.nodes import legal_evidence_match as _legal_evidence_match_module
from app.graphs.contract_review.nodes.parse_contract import parse_contract_node
from app.graphs.contract_review.nodes.report_generate import report_generate_node
from app.graphs.contract_review.nodes.risk_detect import risk_detect_node
from app.graphs.contract_review.nodes.suggestion_generate import suggestion_generate_node
from app.graphs.contract_review.nodes.common import _append_trace, _copy_state, _set_step
from app.graphs.contract_review.state import STEP_SEQUENCE
from app.rag import LegalEvidenceRetriever


def legal_evidence_match_node(state: ContractReviewState) -> ContractReviewState:
    _legal_evidence_match_module.LegalEvidenceRetriever = LegalEvidenceRetriever
    return _legal_evidence_match_module.legal_evidence_match_node(state)


__all__ = [
    "ARTIFACT_PATHS",
    "ContractReviewState",
    "LegalContractReviewStateGraphRuntime",
    "LegalEvidenceRetriever",
    "STEP_SEQUENCE",
    "WORKFLOW_ID",
    "_append_evidence_appendix",
    "_append_trace",
    "_artifacts",
    "_copy_state",
    "_evidence_items",
    "_evidence_trace_payload",
    "_fallback_evidence_for_risk",
    "_mock_parse_contract_output",
    "_risk_items",
    "_set_step",
    "build_contract_review_graph",
    "classify_clauses_node",
    "human_review_node",
    "legal_evidence_match_node",
    "parse_contract_node",
    "read_artifact",
    "report_generate_node",
    "risk_detect_node",
    "suggestion_generate_node",
    "write_artifact",
]
