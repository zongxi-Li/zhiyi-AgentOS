from __future__ import annotations

from typing import Any, Dict

from app.graphs.contract_review.state import ContractReviewState


PARSE_CONTRACT = "parse_contract"
CLASSIFY_CLAUSES = "classify_clauses"
RISK_DETECT = "risk_detect"
LEGAL_EVIDENCE_MATCH = "legal_evidence_match"
SUGGESTION_GENERATE = "suggestion_generate"
HUMAN_REVIEW = "human_review"
REPORT_GENERATE = "report_generate"

ARTIFACT_PATHS = {
    "risks": "output.artifacts.risk_detect.risks",
    "evidences": "output.artifacts.legal_evidence_match.evidences",
    "report": "output.artifacts.report_generate.report_markdown",
}


def ensure_artifacts(state: ContractReviewState) -> Dict[str, Any]:
    artifacts = dict(state.get("artifacts", {}))
    state["artifacts"] = artifacts
    return artifacts


def read_artifact(state: ContractReviewState, key: str, default: Any = None) -> Any:
    return ensure_artifacts(state).get(key, default)


def write_artifact(state: ContractReviewState, key: str, value: Dict[str, Any]) -> Dict[str, Any]:
    ensure_artifacts(state)[key] = value
    return value


def _artifacts(state: ContractReviewState) -> Dict[str, Any]:
    return ensure_artifacts(state)
