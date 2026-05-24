from __future__ import annotations

from typing import Any, Dict, List, Optional

from typing_extensions import TypedDict


WORKFLOW_ID = "legal_contract_review_stategraph_v1"


class ContractReviewState(TypedDict, total=False):
    run_id: str
    workflow_id: str
    contract_text: str
    current_step: Optional[str]
    status: str
    steps: Dict[str, Dict[str, Any]]
    risks: List[Dict[str, Any]]
    evidences: List[Dict[str, Any]]
    traces: List[Dict[str, Any]]
    review: Dict[str, Any]
    artifacts: Dict[str, Any]
    report_markdown: str
    error: Optional[str]


STEP_SEQUENCE = [
    "parse_contract",
    "classify_clauses",
    "risk_detect",
    "legal_evidence_match",
    "suggestion_generate",
    "human_review",
    "report_generate",
]
