from __future__ import annotations

from typing import Any, Dict

from app.llm.schemas import compact_schema_name


class MockLLMProvider:
    provider_name = "mock"
    model = "mock-contract-review"

    def generate_text(self, prompt: str, **kwargs) -> str:
        return "Mock provider response."

    def generate_json(self, prompt: str, schema: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        task = compact_schema_name(schema)
        if task == "chat_route_decision":
            user_text = prompt
            if "用户输入：" in prompt:
                user_text = prompt.split("用户输入：", 1)[1].splitlines()[0]
            prompt_lower = user_text.lower()
            if any(marker in prompt_lower for marker in ["你是什么模型", "你用什么模型", "什么大模型", "底层模型", "模型是什么"]):
                return {
                    "decision": "direct",
                    "workflow_id": "none",
                    "use_langgraph": False,
                    "reason": "用户询问底层模型或系统身份，不需要启动工作流。",
                    "confidence": 0.96,
                    "direct_answer_type": "model_intro",
                }
            if any(marker in prompt_lower for marker in ["你好", "您好", "你是什么角色", "你是谁", "what are you"]):
                return {
                    "decision": "direct",
                    "workflow_id": "none",
                    "use_langgraph": False,
                    "reason": "用户是在问候或询问智能体角色，不需要启动工作流。",
                    "confidence": 0.96,
                    "direct_answer_type": "role_intro",
                }
            if any(marker in prompt_lower for marker in ["使用vpn违法吗", "vpn违法吗", "翻墙违法吗"]):
                return {
                    "decision": "direct",
                    "workflow_id": "none",
                    "use_langgraph": False,
                    "reason": "用户提出一般法律咨询，不需要合同审查图流程。",
                    "confidence": 0.9,
                    "direct_answer_type": "general_question",
                }
            if any(marker in prompt_lower for marker in ["审查这份", "合同审查", "审查合同", "软件开发合同", "软件开发服务合同"]):
                return {
                    "decision": "workflow",
                    "workflow_id": "legal_contract_review_v1",
                    "use_langgraph": True,
                    "reason": "用户明确要求审查合同，需要进入 LangGraph 合同审查流程。",
                    "confidence": 0.92,
                    "direct_answer_type": "none",
                }
            return {
                "decision": "workflow",
                "workflow_id": "legacy_default",
                "use_langgraph": False,
                "reason": "用户提出需要专业 Agent 处理的任务。",
                "confidence": 0.72,
                "direct_answer_type": "none",
            }
        if task == "parse_contract":
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
                "summary": "合同围绕 CRM 系统开发、付款、验收和源代码权属作出基础约定。",
            }
        if task == "risk_detect":
            return {
                "risks": [
                    {
                        "id": "risk-payment-01",
                        "title": "尾款支付条件过于单一",
                        "level": "high",
                        "clause": "系统上线后支付 70%。",
                        "reason": "基于合同文本本身，上线不等于验收完成，尾款触发条件缺少缺陷修复和验收确认约束。",
                        "consequence": "系统存在缺陷时，双方可能就是否应支付尾款产生争议。",
                        "suggestion": "将尾款支付条件改为验收通过并稳定运行一定期间后支付。",
                        "evidenceIds": [],
                    },
                    {
                        "id": "risk-acceptance-01",
                        "title": "验收标准缺少客观指标",
                        "level": "medium",
                        "clause": "如无重大问题视为验收通过。",
                        "reason": "基于合同文本本身，重大问题未定义，缺少测试标准、反馈期限和整改次数。",
                        "consequence": "双方可能对缺陷严重程度和验收是否通过产生争议。",
                        "suggestion": "补充功能清单、性能指标、验收材料、反馈期限和整改流程。",
                        "evidenceIds": [],
                    },
                    {
                        "id": "risk-ip-01",
                        "title": "知识产权共同所有安排不清",
                        "level": "high",
                        "clause": "项目源代码归双方共同所有。",
                        "reason": "基于合同文本本身，共同所有未说明使用、转让、二次开发和第三方组件边界。",
                        "consequence": "后续系统迭代、商业化或对外交付源码时可能出现权属冲突。",
                        "suggestion": "分别约定定制成果归属、乙方通用工具保留权利和第三方组件合规责任。",
                        "evidenceIds": [],
                    },
                ]
            }
        if task == "report_generate":
            return {
                "report_markdown": """# 软件开发服务合同审查报告

## 合同基本信息
- 合同类型：软件开发服务合同
- 审查范围：付款、验收、知识产权和交付责任

## 风险摘要
当前识别到高风险 2 项、中风险 1 项。风险判断仅基于合同文本本身。

## 风险条款列表
1. 尾款支付条件过于单一
2. 验收标准缺少客观指标
3. 知识产权共同所有安排不清

## 修改建议
- 将尾款支付与验收通过、稳定运行和缺陷修复挂钩。
- 补充验收标准、测试材料、反馈期限和整改流程。
- 明确定制成果、通用工具和第三方组件的权利边界。

## 人工审核状态
已通过人工审核后生成报告。

## 免责声明
当前报告未接入正式法律法规 RAG，法律依据部分仅为演示或待补充；本报告不构成最终法律意见，需律师复核。
"""
            }
        return {}
