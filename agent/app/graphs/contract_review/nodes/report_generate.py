from __future__ import annotations

from typing import Any, Dict

from agentos.core.models.types import ReviewDecisionType, StepStatus, TraceEventType, WorkflowStatus
from app.llm.prompts import render_report_generate_prompt
from app.llm.schemas import REPORT_GENERATE_SCHEMA
from app.graphs.contract_review.artifacts import REPORT_GENERATE, _artifacts, write_artifact
from app.graphs.contract_review.mock_data import _append_evidence_appendix
from app.graphs.contract_review.nodes.common import (
    _append_trace,
    _copy_state,
    _gateway_json_or_fallback,
    _set_step,
)
from app.graphs.contract_review.state import ContractReviewState


def _validate_report_generate_output(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict) or not isinstance(data.get("report_markdown"), str):
        raise ValueError("report_generate output must contain report_markdown")
    report = data["report_markdown"].strip()
    if not report:
        raise ValueError("report_markdown is empty")
    disclaimer = "当前报告未接入正式法律法规 RAG，法律依据部分仅为演示或待补充；本报告不构成最终法律意见，需律师复核。"
    if "未接入正式法律法规 RAG" not in report:
        report = f"{report.rstrip()}\n\n## 免责声明\n{disclaimer}\n"
    return {"report_markdown": report}


def report_generate_node(state: ContractReviewState) -> ContractReviewState:
    state = _copy_state(state)
    review = dict(state.get("review", {}))
    if review.get("status") != ReviewDecisionType.APPROVED.value:
        state["status"] = WorkflowStatus.FAILED.value
        state["error"] = "Report generation requires approved human review."
        _set_step(state, "report_generate", StepStatus.FAILED.value, {"error": state["error"]})
        _append_trace(state, step_id="report_generate", event_type=TraceEventType.STEP_FAILED.value, observation=state["error"])
        return state

    risks = state.get("risks", [])
    evidences = state.get("evidences", [])
    risk_lines = "\n".join(
        f"{index}. {risk.get('title')}：{risk.get('reason')}\n   建议：{risk.get('suggestion')}"
        for index, risk in enumerate(risks, start=1)
    )
    evidence_lines = "\n".join(
        f"{index}. {item.get('sourceName')}：{item.get('citationText')}（演示依据 / 待正式法律知识库校验）"
        for index, item in enumerate(evidences, start=1)
    )
    report_markdown = f"""# 软件开发服务合同审查报告

## 一、审查结论
合同具备基础交易结构，但付款、验收和知识产权条款需要在签署前补强。

## 二、风险点
{risk_lines}

## 三、Evidence 依据链
{evidence_lines}

## 四、人工审核
审核结论：approved
审核意见：{review.get('comment', '')}
"""
    report_result, llm_trace = _gateway_json_or_fallback(
        node_name="report_generate",
        prompt=render_report_generate_prompt(
            {
                "artifacts": _artifacts(state),
                "risks": risks,
                "evidences": evidences,
                "review": review,
            }
        ),
        schema=REPORT_GENERATE_SCHEMA,
        fallback=_validate_report_generate_output({"report_markdown": report_markdown}),
        validator=_validate_report_generate_output,
    )
    report_markdown = report_result["report_markdown"]
    report_markdown = _append_evidence_appendix(report_markdown, evidences)
    output = {
        "report_markdown": report_markdown,
        "report": {
            "riskItems": risks,
            "evidenceAppendix": evidences,
            "reviewStatus": "approved",
        },
    }
    state["status"] = WorkflowStatus.COMPLETED.value
    state["current_step"] = None
    state["report_markdown"] = report_markdown
    write_artifact(state, REPORT_GENERATE, output)
    _set_step(state, "human_review", StepStatus.COMPLETED.value, _artifacts(state).get("human_review", {}))
    _set_step(state, "report_generate", StepStatus.COMPLETED.value, output)
    state["current_step"] = None
    _append_trace(state, step_id="report_generate", event_type=TraceEventType.AGENT_CALLED.value, observation="Contract review report generated.", payload=llm_trace)
    return state
