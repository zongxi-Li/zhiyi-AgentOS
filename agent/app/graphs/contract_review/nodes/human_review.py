from __future__ import annotations

from agentos.core.models.types import StepStatus, TraceEventType, WorkflowStatus
from app.graphs.contract_review.artifacts import HUMAN_REVIEW, _artifacts, write_artifact
from app.graphs.contract_review.nodes.common import _append_trace, _copy_state, _set_step
from app.graphs.contract_review.state import ContractReviewState


def human_review_node(state: ContractReviewState) -> ContractReviewState:
    state = _copy_state(state)
    output = {
        "review_status": "pending",
        "reviewer": "demo.lawyer",
        "review_focus": _artifacts(state).get("suggestion_generate", {}).get("manual_review_focus", []),
        "risks": state.get("risks", []),
        "message": "等待律师或业务负责人确认风险结论后进入报告生成。",
    }
    state["status"] = WorkflowStatus.WAITING_REVIEW.value
    state["review"] = output
    write_artifact(state, HUMAN_REVIEW, output)
    _set_step(state, "human_review", StepStatus.WAITING_REVIEW.value, output)
    _append_trace(state, step_id="human_review", event_type=TraceEventType.REVIEW_REQUIRED.value, observation="Human review required before report generation.", payload=output)
    return state
