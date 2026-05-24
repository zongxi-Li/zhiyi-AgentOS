from __future__ import annotations

from typing import Any, Dict, List

from agentos.core.models.types import StepStatus, TraceEventType
from app.llm.prompts import render_risk_detect_prompt
from app.llm.schemas import RISK_DETECT_SCHEMA
from app.graphs.contract_review.artifacts import RISK_DETECT, _artifacts, write_artifact
from app.graphs.contract_review.mock_data import _risk_items
from app.graphs.contract_review.nodes.common import (
    _append_trace,
    _copy_state,
    _gateway_json_or_fallback,
    _set_step,
)
from app.graphs.contract_review.state import ContractReviewState


def _validate_risk_detect_output(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict) or not isinstance(data.get("risks"), list):
        raise ValueError("risk_detect output must contain risks list")
    risks: List[Dict[str, Any]] = []
    for index, item in enumerate(data["risks"], start=1):
        if not isinstance(item, dict):
            continue
        level = str(item.get("level") or "medium").lower()
        if level not in {"high", "medium", "low"}:
            level = "medium"
        risks.append(
            {
                "id": str(item.get("id") or f"risk-{index:02d}"),
                "title": str(item.get("title") or "未命名风险"),
                "level": level,
                "clause": str(item.get("clause") or ""),
                "reason": str(item.get("reason") or "基于合同文本本身，风险原因待补充。"),
                "consequence": str(item.get("consequence") or ""),
                "suggestion": str(item.get("suggestion") or ""),
                "evidenceIds": [],
            }
        )
    if not risks:
        raise ValueError("risk_detect risks list is empty")
    return {"risks": risks}


def risk_detect_node(state: ContractReviewState) -> ContractReviewState:
    state = _copy_state(state)
    risks = _risk_items()
    output = {
        "risks": risks,
        "risk_summary": {
            "high": 2,
            "medium": 1,
            "low": 0,
            "conclusion": "付款、验收和知识产权条款需要在签署前补强。",
        },
        "risk_level": "high",
        "risk_score": 82,
    }
    output, llm_trace = _gateway_json_or_fallback(
        node_name="risk_detect",
        prompt=render_risk_detect_prompt(contract_text=state.get("contract_text", ""), state={"artifacts": _artifacts(state)}),
        schema=RISK_DETECT_SCHEMA,
        fallback={"risks": _risk_items()},
        validator=_validate_risk_detect_output,
    )
    risks = output["risks"]
    risk_counts = {
        "high": sum(1 for risk in risks if risk.get("level") == "high"),
        "medium": sum(1 for risk in risks if risk.get("level") == "medium"),
        "low": sum(1 for risk in risks if risk.get("level") == "low"),
    }
    output["risk_summary"] = {
        **risk_counts,
        "conclusion": "风险判断基于合同文本本身，正式法律依据待 RAG 补充。",
    }
    output["risk_level"] = "high" if risk_counts["high"] else "medium"
    output["risk_score"] = 82 if risk_counts["high"] else 60
    state["risks"] = risks
    write_artifact(state, RISK_DETECT, output)
    _set_step(state, "risk_detect", StepStatus.COMPLETED.value, output)
    _append_trace(state, step_id="risk_detect", event_type=TraceEventType.AGENT_CALLED.value, observation=f"Detected {len(risks)} contract risk item(s).", payload=llm_trace)
    return state
