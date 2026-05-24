from __future__ import annotations

from agentos.core.models.types import StepStatus, TraceEventType
from app.graphs.contract_review.artifacts import CLASSIFY_CLAUSES, write_artifact
from app.graphs.contract_review.nodes.common import _append_trace, _copy_state, _set_step
from app.graphs.contract_review.state import ContractReviewState


def classify_clauses_node(state: ContractReviewState) -> ContractReviewState:
    state = _copy_state(state)
    output = {
        "clauses": [
            {"category": "付款", "attention": "尾款应绑定验收和稳定运行。"},
            {"category": "交付", "attention": "应明确交付物清单和源码交付范围。"},
            {"category": "违约", "attention": "应补充延期、质量缺陷和保密违约责任。"},
            {"category": "解除", "attention": "应明确重大违约、逾期和验收失败时的解除权。"},
            {"category": "争议解决", "attention": "应补充管辖法院或仲裁机构。"},
        ],
        "clause_count": 5,
    }
    write_artifact(state, CLASSIFY_CLAUSES, output)
    _set_step(state, "classify_clauses", StepStatus.COMPLETED.value, output)
    _append_trace(state, step_id="classify_clauses", event_type=TraceEventType.AGENT_CALLED.value, observation="Contract clauses classified.", payload=output)
    return state
