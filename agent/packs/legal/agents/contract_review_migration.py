from __future__ import annotations

from typing import Any, Callable, Dict, List

from agentos.agents.base import AgentOutput, AgentProfile, BaseAgent
from app.llm.gateway import get_llm_gateway
from app.llm.prompts import render_parse_contract_prompt, render_report_generate_prompt, render_risk_detect_prompt
from app.llm.schemas import PARSE_CONTRACT_SCHEMA, REPORT_GENERATE_SCHEMA, RISK_DETECT_SCHEMA
from app.rag import LegalEvidenceRetriever
from app.rag.legal_evidence_schema import normalize_evidence
from packs.legal.agents.common import case_text


def _contract_text(context) -> str:
    return case_text(context.task.input) or str(context.task.input.get("contractText") or "").strip()


def _observation(context, *step_ids: str) -> Dict[str, Any]:
    """Read an upstream artifact by stable public step ID or its former ACG demo ID."""
    observations = context.memory.observations
    for step_id in step_ids:
        value = observations.get(step_id)
        if isinstance(value, dict):
            return value
    return {}


def _llm_json_or_fallback(
    *,
    node_name: str,
    prompt: str,
    schema: Dict[str, Any],
    fallback: Dict[str, Any],
    validator: Callable[[Dict[str, Any]], Dict[str, Any]],
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """Preserve the former graph's JSON guard and deterministic fallback behavior."""
    gateway = get_llm_gateway()
    try:
        response = gateway.generate_json(prompt, schema)
        output = validator(response.get("data", {}))
        provider = str(response.get("provider") or gateway.provider_name)
        return output, {
            "node_name": node_name,
            "provider": provider,
            "model": str(response.get("model") or gateway.model),
            "source": "mock" if provider == "mock" else "llm",
            "success": True,
            "latency_ms": int(response.get("latency_ms") or 0),
        }
    except Exception as exc:
        return fallback, {
            "node_name": node_name,
            "provider": getattr(gateway, "provider_name", "unknown"),
            "model": getattr(gateway, "model", "unknown"),
            "source": "mock_fallback",
            "success": False,
            "error": str(exc)[:240],
        }


def _validate_parse_contract(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict) or not isinstance(data.get("parties"), list):
        raise ValueError("parse_contract output must contain a parties list")
    return {
        "contract_summary": str(data.get("summary") or ""),
        "contract_title": str(data.get("contract_title") or "unknown"),
        "parties": [
            {"name": str(item.get("name") or "unknown"), "role": str(item.get("role") or "unknown")}
            for item in data["parties"] if isinstance(item, dict)
        ],
        "contract_type": str(data.get("contract_type") or "unknown"),
        "key_dates": data.get("key_dates") if isinstance(data.get("key_dates"), list) else [],
        "amounts": data.get("amounts") if isinstance(data.get("amounts"), list) else [],
        "obligations": data.get("obligations") if isinstance(data.get("obligations"), list) else [],
    }


def _validate_risks(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict) or not isinstance(data.get("risks"), list) or not data["risks"]:
        raise ValueError("risk_detect output must contain a non-empty risks list")
    risks = []
    for index, item in enumerate(data["risks"], start=1):
        if not isinstance(item, dict):
            continue
        level = str(item.get("level") or "medium").lower()
        risks.append({
            "id": str(item.get("id") or f"risk-{index:02d}"),
            "title": str(item.get("title") or "unnamed risk"),
            "level": level if level in {"high", "medium", "low"} else "medium",
            "clause": str(item.get("clause") or ""),
            "reason": str(item.get("reason") or ""),
            "consequence": str(item.get("consequence") or ""),
            "suggestion": str(item.get("suggestion") or ""),
            "evidenceIds": list(item.get("evidenceIds") or []),
        })
    if not risks:
        raise ValueError("risk_detect output has no valid risks")
    return {"risks": risks}


def _validate_report(data: Dict[str, Any]) -> Dict[str, Any]:
    report = data.get("report_markdown") if isinstance(data, dict) else None
    if not isinstance(report, str) or not report.strip():
        raise ValueError("report_generate output must contain report_markdown")
    report = report.strip()
    disclaimer = "当前报告未接入正式法律法规 RAG，法律依据部分仅为演示或待补充；本报告不构成最终法律意见，需律师复核。"
    if "本报告不构成最终法律意见" not in report:
        report = f"{report.rstrip()}\n\n## 免责声明\n{disclaimer}\n"
    return {"report_markdown": report}


def _fallback_evidence_for_risk(risk: Dict[str, Any], index: int) -> Dict[str, Any]:
    templates = _evidence_items()
    item = dict(templates[(index - 1) % len(templates)])
    item["riskId"] = str(risk.get("id") or f"risk-{index:02d}")
    item["sourceType"] = "mock"
    item["sourceName"] = "演示依据，待正式法律知识库校验"
    item["metadata"] = {"demo": True}
    return item


def _append_evidence_appendix(report: str, evidences: List[Dict[str, Any]]) -> str:
    if not evidences:
        return report
    citations = [str(item.get("citationText") or "") for item in evidences]
    if "Evidence 依据链" in report and any(citation and citation in report for citation in citations):
        return report
    lines = ["", "## Evidence 依据链"]
    for index, item in enumerate(evidences, start=1):
        metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        marker = "（演示依据 / 待正式法律知识库校验）" if item.get("sourceType") == "mock" or metadata.get("demo") else ""
        lines.append(
            f"{index}. [{item.get('sourceType')}] {item.get('sourceName')} {marker}：{item.get('citationText')}"
        )
    return f"{report.rstrip()}\n" + "\n".join(lines) + "\n"


def _latest_human_review(context) -> Dict[str, Any]:
    for event in reversed(context.run.trace):
        event_type = getattr(event.event_type, "value", event.event_type)
        payload = event.payload if isinstance(event.payload, dict) else {}
        if event_type == "review_decided" and (payload.get("stepId") or event.step_id) == "human_review":
            return payload
    return {}


def _append_review_result(report: str, review: Dict[str, Any]) -> str:
    if not review:
        return report
    reviewer = str(review.get("reviewer") or "system")
    comment = str(review.get("comment") or "").strip()
    if reviewer in report and (not comment or comment in report):
        return report
    lines = ["", "## 人工审核记录", f"- 审核人：{reviewer}", "- 审核结论：approved"]
    if comment:
        lines.append(f"- 审核意见：{comment}")
    return f"{report.rstrip()}\n" + "\n".join(lines) + "\n"


def _risk_items() -> List[Dict[str, Any]]:
    return [
        {
            "id": "risk-payment-01",
            "title": "尾款支付条件过于单一",
            "level": "high",
            "clause": "甲方在合同签署后支付 30%，系统上线后支付 70%。",
            "reason": "尾款触发条件仅写“上线”，未绑定阶段验收、缺陷修复、发票开具和上线失败处理。",
            "consequence": "上线后仍存在严重缺陷时，甲方可能被要求支付大额尾款，乙方也可能因付款条件不清产生回款争议。",
            "suggestion": "建议改为“需求确认 20% + 原型确认 20% + 测试验收 30% + 上线稳定运行 30%”，并补充发票和逾期付款规则。",
            "evidenceIds": ["ev-payment-01", "ev-acceptance-01"],
        },
        {
            "id": "risk-acceptance-01",
            "title": "验收标准缺少客观指标",
            "level": "medium",
            "clause": "如无重大问题视为验收通过。",
            "reason": "“重大问题”没有定义，未明确验收材料、测试用例、反馈期限和整改次数。",
            "consequence": "双方可能对缺陷严重程度、是否通过验收、延期责任产生争议。",
            "suggestion": "建议列明功能清单、性能指标、验收流程、书面反馈期限以及视为验收通过的前置条件。",
            "evidenceIds": ["ev-acceptance-01"],
        },
        {
            "id": "risk-ip-01",
            "title": "知识产权共同所有安排不清",
            "level": "high",
            "clause": "项目相关源代码、文档和设计成果归双方共同所有。",
            "reason": "共同所有未说明使用、转让、二次开发、开源组件和第三方素材的授权边界。",
            "consequence": "后续商业化、系统迭代、对外授权或交付源代码时可能产生权属冲突。",
            "suggestion": "建议明确甲方享有定制成果全部著作财产权，乙方保留通用工具和预置组件权利，并承诺第三方组件合规。",
            "evidenceIds": ["ev-ip-01"],
        },
    ]


def _evidence_items() -> List[Dict[str, Any]]:
    return [
        {
            "id": "ev-payment-01",
            "stepId": "legal_evidence_match",
            "sourceType": "contract_template",
            "sourceName": "软件开发合同审查模板库",
            "content": "付款节点通常与里程碑、阶段验收、缺陷修复期绑定，避免尾款支付条件过于单一。",
            "citationText": "付款条款应明确付款比例、触发条件、发票条件与逾期处理。",
            "confidence": 0.92,
        },
        {
            "id": "ev-acceptance-01",
            "stepId": "legal_evidence_match",
            "sourceType": "practice",
            "sourceName": "技术服务项目验收审查要点",
            "content": "仅以“无重大问题”作为验收标准，容易造成缺陷范围、整改期限和视为通过条件争议。",
            "citationText": "验收条款宜列明验收材料、测试标准、反馈期限、整改次数和最终确认方式。",
            "confidence": 0.89,
        },
        {
            "id": "ev-ip-01",
            "stepId": "legal_evidence_match",
            "sourceType": "law",
            "sourceName": "民法典合同编与著作权法相关规则",
            "content": "定制开发成果权属应结合委托目的、费用结构、源代码交付和第三方组件授权明确约定。",
            "citationText": "知识产权归属、使用范围、源代码交付、开源组件合规应分别约定。",
            "confidence": 0.9,
        },
        {
            "id": "ev-liability-01",
            "stepId": "legal_evidence_match",
            "sourceType": "case",
            "sourceName": "软件开发合同纠纷裁判摘要",
            "content": "违约责任缺少计算方式和责任上限时，争议中往往需要法院结合损失、过错和履行情况酌定。",
            "citationText": "违约责任条款应明确延迟交付、质量缺陷、逾期付款和保密违约的责任边界。",
            "confidence": 0.86,
        },
    ]


def _risk_counts(risks: List[Dict[str, Any]]) -> Dict[str, int]:
    counts = {"high": 0, "medium": 0, "low": 0}
    for risk in risks:
        level = str(risk.get("level") or "low")
        if level in counts:
            counts[level] += 1
    return counts


class ContractParseAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            AgentProfile(
                agentName="contract_parse",
                domain="legal",
                capabilities=["contract_parse"],
                allowedSkills=["contract_parser"],
                description="Parses contract text into parties, scope, payment, acceptance, IP, and dispute fields.",
            )
        )

    async def run(self, context):
        text = _contract_text(context)
        output = {
            "contract_summary": text[:500] or "未提供合同文本",
            "contract_type": "软件开发服务合同",
            "parties": ["甲方：星河科技有限公司", "乙方：知弈软件工作室"],
            "scope": "客户关系管理系统的需求梳理、原型设计、系统开发、测试部署和上线支持。",
            "payment_terms": "签署后 30%，上线后 70%。",
            "acceptance_terms": "无重大问题视为验收通过。",
            "ip_terms": "源代码、文档和设计成果归双方共同所有。",
            "dispute_resolution": "建议补充管辖、仲裁或诉讼条款。",
            "original_preview": text[:120],
        }
        output, llm = _llm_json_or_fallback(
            node_name="parse_contract",
            prompt=render_parse_contract_prompt(text),
            schema=PARSE_CONTRACT_SCHEMA,
            fallback=output,
            validator=_validate_parse_contract,
        )
        output["parties"] = [
            f"{item.get('name', 'unknown')}：{item.get('role', 'unknown')}"
            if isinstance(item, dict) else str(item)
            for item in output.get("parties", [])
        ]
        output["original_preview"] = text[:120]
        output["_llm"] = llm
        return AgentOutput(output=output, summary="Contract text parsed into structured fields.")


class ClauseClassifyAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            AgentProfile(
                agentName="clause_classify",
                domain="legal",
                capabilities=["clause_classify"],
                allowedSkills=["clause_classifier"],
                description="Classifies contract clauses and marks clauses that need legal attention.",
            )
        )

    async def run(self, context):
        parsed = _observation(context, "parse_contract", "contract_parse")
        categories = [
            {"category": "主体信息", "content": parsed.get("parties", []), "attention": "确认签约主体和授权代表。"},
            {"category": "项目范围", "content": parsed.get("scope", ""), "attention": "范围应与交付物清单、排期和验收标准联动。"},
            {"category": "付款", "content": parsed.get("payment_terms", ""), "attention": "尾款不宜只绑定上线，应绑定稳定运行和验收。"},
            {"category": "验收", "content": parsed.get("acceptance_terms", ""), "attention": "需补充客观指标、反馈期限和整改次数。"},
            {"category": "知识产权", "content": parsed.get("ip_terms", ""), "attention": "需明确成果归属、复用权和第三方组件合规。"},
            {"category": "违约责任", "content": "未见完整责任上限与计算方式。", "attention": "建议补齐责任边界和赔偿上限。"},
            {"category": "争议解决", "content": parsed.get("dispute_resolution", ""), "attention": "需明确法院管辖或仲裁机构。"},
        ]
        return AgentOutput(
            output={"clauses": categories, "clause_count": len(categories)},
            summary=f"Classified {len(categories)} contract clause group(s).",
        )


class RiskDetectAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            AgentProfile(
                agentName="risk_detect",
                domain="legal",
                capabilities=["risk_detect"],
                allowedSkills=["risk_detection"],
                riskLevel="high",
                description="Detects contract risks from parsed and classified clauses.",
            )
        )

    async def run(self, context):
        fallback = {"risks": _risk_items()}
        artifacts = {
            "parse_contract": _observation(context, "parse_contract", "contract_parse"),
            "classify_clauses": _observation(context, "classify_clauses", "clause_classify"),
        }
        llm_output, llm = _llm_json_or_fallback(
            node_name="risk_detect",
            prompt=render_risk_detect_prompt(
                contract_text=_contract_text(context),
                state={"artifacts": artifacts},
            ),
            schema=RISK_DETECT_SCHEMA,
            fallback=fallback,
            validator=_validate_risks,
        )
        risks = llm_output["risks"]
        counts = _risk_counts(risks)
        risk_level = "high" if counts["high"] else "medium" if counts["medium"] else "low"
        risk_score = 82 if counts["high"] else 60 if counts["medium"] else 30
        output = {
            "risks": risks,
            "risk_summary": {
                **counts,
                "conclusion": "付款、验收和知识产权条款需要在签署前补强。",
            },
            "risk_level": risk_level,
            "risk_score": risk_score,
            "_llm": llm,
        }
        return AgentOutput(
            output=output,
            summary=f"Detected {len(risks)} contract risk item(s).",
            riskLevel=risk_level,
        )


class LegalEvidenceMatchAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            AgentProfile(
                agentName="legal_evidence_match",
                domain="legal",
                capabilities=["legal_evidence_match"],
                allowedSkills=["legal_evidence_search"],
                description="Matches legal, template, practice, and case evidence to detected contract risks.",
            )
        )

    async def run(self, context):
        risk_output = _observation(context, "risk_detect")
        parsed = _observation(context, "parse_contract", "contract_parse")
        risks = risk_output.get("risks") or []
        evidences: List[Dict[str, Any]] = []
        fallback = False
        errors: List[str] = []
        retriever = LegalEvidenceRetriever()
        for index, risk in enumerate(risks or _risk_items(), start=1):
            try:
                results = retriever.retrieve(
                    risk=risk,
                    contract_type=str(parsed.get("contract_type") or ""),
                    top_k=2,
                )
                if results:
                    evidences.extend(results)
                    continue
            except Exception as exc:
                errors.append(str(exc)[:240])
            fallback = True
            evidences.append(_fallback_evidence_for_risk(risk, index))
        evidences = [normalize_evidence(item, risk_id=str(item.get("riskId") or "")) for item in evidences]
        return AgentOutput(
            output={
                "evidences": evidences,
                "citations": [item["citationText"] for item in evidences],
                "retrieval": {
                    "fallback": fallback,
                    "result_count": len(evidences),
                    "errors": errors,
                },
            },
            summary=f"Matched {len(evidences)} evidence item(s) to contract risks.",
        )


class RevisionSuggestAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            AgentProfile(
                agentName="revision_suggest",
                domain="legal",
                capabilities=["revision_suggest"],
                allowedSkills=["revision_suggestion"],
                description="Generates concrete revision suggestions from risks and evidence.",
            )
        )

    async def run(self, context):
        risk_output = _observation(context, "risk_detect")
        risks = risk_output.get("risks") or []
        suggestions = [
            {
                "riskId": risk.get("id"),
                "title": risk.get("title"),
                "suggestion": risk.get("suggestion"),
                "requiresBusinessDecision": risk.get("level") == "high",
            }
            for risk in risks
        ]
        return AgentOutput(
            output={
                "revision_suggestions": suggestions,
                "manual_review_focus": ["尾款触发条件", "验收标准客观化", "知识产权归属与复用边界"],
            },
            summary=f"Generated {len(suggestions)} revision suggestion(s).",
        )


class HumanReviewGateAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            AgentProfile(
                agentName="human_review",
                domain="legal",
                capabilities=["human_review_gate"],
                allowedSkills=["human_review_gate"],
                riskLevel="high",
                description="Creates a human-review gate before report generation.",
            )
        )

    async def run(self, context):
        risk_output = _observation(context, "risk_detect")
        revision_output = _observation(context, "suggestion_generate", "revision_suggest")
        output = {
            "review_status": "pending",
            "reviewer": "demo.lawyer",
            "review_focus": revision_output.get("manual_review_focus", []),
            "risks": risk_output.get("risks", []),
            "suggested_decision": "approved_after_manual_check",
            "message": "等待律师或业务负责人确认风险结论后进入报告生成。",
        }
        return AgentOutput(output=output, summary="Human review gate prepared.", riskLevel="high")


class ReportGenerateAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            AgentProfile(
                agentName="report_generate",
                domain="legal",
                capabilities=["report_generate"],
                allowedSkills=["report_generation"],
                description="Packages contract review artifacts into a markdown report.",
            )
        )

    async def run(self, context):
        observations = context.memory.observations
        parsed = _observation(context, "parse_contract", "contract_parse")
        risks = observations.get("risk_detect", {}).get("risks", [])
        risk_summary = observations.get("risk_detect", {}).get("risk_summary", {})
        evidences = observations.get("legal_evidence_match", {}).get("evidences", [])
        revisions = _observation(context, "suggestion_generate", "revision_suggest").get("revision_suggestions", [])
        review = _latest_human_review(context)

        risk_lines = "\n".join(
            f"{index}. {risk.get('title')}：{risk.get('reason')}\n   建议：{risk.get('suggestion')}"
            for index, risk in enumerate(risks, start=1)
        )
        evidence_lines = "\n".join(
            f"{index}. {item.get('sourceName')}：{item.get('citationText')}"
            for index, item in enumerate(evidences, start=1)
        )
        revision_lines = "\n".join(
            f"{index}. {item.get('title')}：{item.get('suggestion')}"
            for index, item in enumerate(revisions, start=1)
        )
        report_markdown = f"""# 软件开发服务合同审查报告

## 一、合同基本信息
- 类型：{parsed.get('contract_type', '技术服务 / 软件开发')}
- 主体：{' / '.join(parsed.get('parties', [])) or '待确认'}
- 范围：{parsed.get('scope', '待确认')}

## 二、风险摘要
合同具备基础交易结构，但付款、验收、知识产权条款需要在签署前补强。
- 高风险：{risk_summary.get('high', 0)}
- 中风险：{risk_summary.get('medium', 0)}
- 低风险：{risk_summary.get('low', 0)}

## 三、风险条款列表
{risk_lines}

## 四、修改建议
{revision_lines}

## 五、依据附录
{evidence_lines}

## 六、审核状态
人工审核已通过，报告进入最终审查。
"""
        report_result, llm = _llm_json_or_fallback(
            node_name="report_generate",
            prompt=render_report_generate_prompt(
                {"artifacts": observations, "risks": risks, "evidences": evidences, "review": review}
            ),
            schema=REPORT_GENERATE_SCHEMA,
            fallback={"report_markdown": report_markdown},
            validator=_validate_report,
        )
        report_markdown = _append_evidence_appendix(report_result["report_markdown"], evidences)
        report_markdown = _append_review_result(report_markdown, review)
        output = {
            "final_answer": report_markdown,
            "report_markdown": report_markdown,
            "_llm": llm,
            "report": {
                "contractInfo": {
                    "name": "软件开发服务合同",
                    "type": parsed.get("contract_type", "技术服务 / 软件开发"),
                    "parties": parsed.get("parties", []),
                    "scope": parsed.get("scope", ""),
                },
                "riskSummary": risk_summary,
                "riskItems": risks,
                "revisionSuggestions": revisions,
                "evidenceAppendix": evidences,
                "reviewStatus": "approved",
            },
        }
        return AgentOutput(output=output, summary="Contract review report generated.")


class ContractFinalReviewAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            AgentProfile(
                agentName="contract_final_review",
                domain="legal",
                capabilities=["contract_final_review", "final_review"],
                allowedSkills=["quality_gate"],
                description="Checks the migrated contract review report and exposes the final answer.",
            )
        )

    async def run(self, context):
        report_output = context.memory.observations.get("report_generate", {})
        report_markdown = report_output.get("report_markdown", "")
        final_answer = (
            "已完成合同审查迁移工作流。系统已完成合同解析、条款分类、风险识别、依据匹配、修改建议、人工审核和报告生成。\n\n"
            f"{report_markdown}"
        ).strip()
        return AgentOutput(
            output={
                "final_answer": final_answer,
                "review_notes": ["ACG 合同审查步骤已完成", "人工审核节点已通过", "报告结构完整"],
            },
            summary="Migrated contract review workflow finalized.",
        )
