from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.rag.legal_evidence_schema import normalize_evidence


def _mock_parse_contract_output(text: str) -> Dict[str, Any]:
    return {
        "contract_title": "软件开发服务合同",
        "parties": [
            {"name": "甲方", "role": "委托方"},
            {"name": "乙方", "role": "开发服务方"},
        ],
        "contract_type": "软件开发服务合同",
        "key_dates": [],
        "amounts": ["签署后 30%", "上线后 70%"],
        "obligations": ["开发 CRM 系统", "完成上线交付", "配合验收"],
        "summary": (text[:220] if text else "未提供合同文本。"),
    }


def _risk_items() -> List[Dict[str, Any]]:
    return [
        {
            "id": "risk-payment-01",
            "title": "尾款支付条件过于单一",
            "level": "high",
            "clause": "合同签署后支付 30%，系统上线后支付 70%。",
            "reason": "尾款触发条件只绑定上线，缺少验收、缺陷修复、发票和上线失败处理。",
            "consequence": "上线后仍存在严重缺陷时，付款与整改责任容易发生争议。",
            "suggestion": "",
            "evidenceIds": ["ev-payment-01", "ev-acceptance-01"],
        },
        {
            "id": "risk-acceptance-01",
            "title": "验收标准缺少客观指标",
            "level": "medium",
            "clause": "如无重大问题视为验收通过。",
            "reason": "重大问题没有定义，也未写明验收材料、测试用例、反馈期限和整改次数。",
            "consequence": "双方可能对缺陷严重程度、是否通过验收和延期责任产生争议。",
            "suggestion": "",
            "evidenceIds": ["ev-acceptance-01"],
        },
        {
            "id": "risk-ip-01",
            "title": "知识产权共同所有安排不清",
            "level": "high",
            "clause": "项目源代码归双方共同所有。",
            "reason": "共同所有未说明使用、转让、二次开发、开源组件和第三方素材的授权边界。",
            "consequence": "后续商业化、系统迭代或对外交付源码时可能产生权属冲突。",
            "suggestion": "",
            "evidenceIds": ["ev-ip-01"],
        },
    ]


def _evidence_items() -> List[Dict[str, Any]]:
    items = [
        {
            "id": "ev-payment-01",
            "stepId": "legal_evidence_match",
            "riskId": "risk-payment-01",
            "sourceType": "mock",
            "sourceName": "演示依据，待 RAG 接入",
            "title": "软件开发合同审查模板库",
            "content": "付款节点通常应与里程碑、阶段验收和缺陷修复期绑定。",
            "citationText": "付款条款应明确付款比例、触发条件、发票条件与逾期处理。",
            "chunkId": "",
            "confidence": 0.92,
            "retrievalScore": 0.0,
            "metadata": {"lawName": "", "articleNo": "", "sourcePath": "", "demo": True},
        },
        {
            "id": "ev-acceptance-01",
            "stepId": "legal_evidence_match",
            "riskId": "risk-acceptance-01",
            "sourceType": "mock",
            "sourceName": "演示依据，待 RAG 接入",
            "title": "技术服务项目验收审查要点",
            "content": "仅以无重大问题作为验收标准，容易造成缺陷范围和整改期限争议。",
            "citationText": "验收条款宜列明验收材料、测试标准、反馈期限和最终确认方式。",
            "chunkId": "",
            "confidence": 0.89,
            "retrievalScore": 0.0,
            "metadata": {"lawName": "", "articleNo": "", "sourcePath": "", "demo": True},
        },
        {
            "id": "ev-ip-01",
            "stepId": "legal_evidence_match",
            "riskId": "risk-ip-01",
            "sourceType": "mock",
            "sourceName": "演示依据，待 RAG 接入",
            "title": "民法典合同编与著作权相关规则",
            "content": "定制开发成果权属应结合委托目的、费用结构和源码交付明确约定。",
            "citationText": "知识产权归属、使用范围、源码交付和开源组件合规应分别约定。",
            "chunkId": "",
            "confidence": 0.9,
            "retrievalScore": 0.0,
            "metadata": {"lawName": "", "articleNo": "", "sourcePath": "", "demo": True},
        },
    ]
    return [normalize_evidence(item, risk_id=str(item.get("riskId") or "")) for item in items]


def _fallback_evidence_for_risk(risk: Dict[str, Any], index: int) -> Dict[str, Any]:
    fallback_items = _evidence_items()
    risk_id = str(risk.get("id") or f"risk-{index:02d}")
    matched = next((item for item in fallback_items if item.get("riskId") == risk_id), None)
    if matched is None:
        matched = fallback_items[(index - 1) % len(fallback_items)]
    item = dict(matched)
    item["id"] = str(item.get("id") or f"ev-mock-{index:02d}")
    item["riskId"] = risk_id
    item["sourceType"] = "mock"
    item["sourceName"] = "演示依据，待正式法律知识库校验"
    item["metadata"] = {"lawName": "", "articleNo": "", "sourcePath": "", "demo": True}
    return normalize_evidence(item, risk_id=risk_id)


def _evidence_trace_payload(
    *,
    result_count: int,
    fallback: bool,
    error: Optional[str] = None,
    top_k: int = 2,
) -> Dict[str, Any]:
    payload = {
        "retriever_type": "keyword",
        "top_k": top_k,
        "result_count": result_count,
        "fallback": fallback,
    }
    if error:
        payload["error"] = str(error)[:240]
    return payload


def _append_evidence_appendix(report: str, evidences: List[Dict[str, Any]]) -> str:
    if not evidences:
        return report
    if "Evidence 依据链" in report and any(str(item.get("citationText") or "") in report for item in evidences):
        return report
    lines = ["", "## Evidence 依据链"]
    for index, item in enumerate(evidences, start=1):
        marker = ""
        metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        if item.get("sourceType") == "mock" or metadata.get("demo"):
            marker = "（演示依据 / 待正式法律知识库校验）"
        lines.append(
            f"{index}. [{item.get('sourceType')}] {item.get('sourceName')} {marker}：{item.get('citationText')}"
        )
    return f"{report.rstrip()}\n" + "\n".join(lines) + "\n"
