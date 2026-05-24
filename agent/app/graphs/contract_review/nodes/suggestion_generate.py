from __future__ import annotations

from agentos.core.models.types import StepStatus, TraceEventType
from app.graphs.contract_review.artifacts import SUGGESTION_GENERATE, _artifacts, write_artifact
from app.graphs.contract_review.nodes.common import _append_trace, _copy_state, _set_step
from app.graphs.contract_review.state import ContractReviewState


def suggestion_generate_node(state: ContractReviewState) -> ContractReviewState:
    state = _copy_state(state)
    suggestions = {
        "risk-payment-01": "改为需求确认 20% + 原型确认 20% + 测试验收 30% + 稳定运行 30%，并补充发票和逾期规则。",
        "risk-acceptance-01": "列明功能清单、性能指标、验收流程、书面反馈期限和视为验收通过的前置条件。",
        "risk-ip-01": "明确甲方享有定制成果著作财产权，乙方保留通用工具权利，并承诺第三方组件合规。",
    }
    risks = []
    for risk in state.get("risks", []):
        item = dict(risk)
        item["suggestion"] = suggestions.get(str(item.get("id")), "")
        risks.append(item)
    output = {
        "revision_suggestions": [
            {
                "riskId": risk.get("id"),
                "title": risk.get("title"),
                "suggestion": risk.get("suggestion"),
                "requiresBusinessDecision": risk.get("level") == "high",
            }
            for risk in risks
        ],
        "manual_review_focus": ["尾款触发条件", "验收标准客观化", "知识产权归属与复用边界"],
    }
    state["risks"] = risks
    _artifacts(state)["risk_detect"]["risks"] = risks
    write_artifact(state, SUGGESTION_GENERATE, output)
    _set_step(state, "suggestion_generate", StepStatus.COMPLETED.value, output)
    _append_trace(state, step_id="suggestion_generate", event_type=TraceEventType.AGENT_CALLED.value, observation="Generated revision suggestions.", payload=output)
    return state
