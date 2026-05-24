from __future__ import annotations

from typing import Any, Dict, List

from agentos.core.models.types import StepStatus, TraceEventType
from app.llm.prompts import render_parse_contract_prompt
from app.llm.schemas import PARSE_CONTRACT_SCHEMA
from app.graphs.contract_review.artifacts import PARSE_CONTRACT, write_artifact
from app.graphs.contract_review.mock_data import _mock_parse_contract_output
from app.graphs.contract_review.nodes.common import (
    _append_trace,
    _copy_state,
    _gateway_json_or_fallback,
    _set_step,
)
from app.graphs.contract_review.state import ContractReviewState


def _validate_parse_contract_output(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("parse_contract output must be an object")
    parties = data.get("parties")
    if not isinstance(parties, list):
        raise ValueError("parse_contract.parties must be a list")
    return {
        "contract_title": str(data.get("contract_title") or "unknown"),
        "parties": [
            {
                "name": str(item.get("name") or "unknown") if isinstance(item, dict) else "unknown",
                "role": str(item.get("role") or "unknown") if isinstance(item, dict) else "unknown",
            }
            for item in parties
        ],
        "contract_type": str(data.get("contract_type") or "unknown"),
        "key_dates": data.get("key_dates") if isinstance(data.get("key_dates"), list) else [],
        "amounts": data.get("amounts") if isinstance(data.get("amounts"), list) else [],
        "obligations": data.get("obligations") if isinstance(data.get("obligations"), list) else [],
        "summary": str(data.get("summary") or "unknown"),
    }


def parse_contract_node(state: ContractReviewState) -> ContractReviewState:
    state = _copy_state(state)
    text = state.get("contract_text", "")
    output = {
        "contract_summary": text[:500] or "未提供合同文本。",
        "contract_type": "软件开发服务合同",
        "parties": ["甲方：委托方", "乙方：开发服务方"],
        "scope": "CRM 系统需求梳理、原型设计、系统开发、测试部署和上线支持。",
        "payment_terms": "签署后 30%，上线后 70%。",
        "acceptance_terms": "无重大问题视为验收通过。",
        "ip_terms": "源代码归双方共同所有。",
    }
    output, llm_trace = _gateway_json_or_fallback(
        node_name="parse_contract",
        prompt=render_parse_contract_prompt(text),
        schema=PARSE_CONTRACT_SCHEMA,
        fallback=_mock_parse_contract_output(text),
        validator=_validate_parse_contract_output,
    )
    write_artifact(state, PARSE_CONTRACT, output)
    _set_step(state, "parse_contract", StepStatus.COMPLETED.value, output)
    _append_trace(state, step_id="parse_contract", event_type=TraceEventType.AGENT_CALLED.value, observation="Contract parsed.", payload=llm_trace)
    return state
