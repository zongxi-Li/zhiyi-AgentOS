"""意图解析器（设计书 §2.1「意图解析」）。

把用户原始自然语言意图解析为结构化 TaskSemanticProfile。

Core 不直接依赖 app 层 LLM 网关（分层铁律）。这里定义最小 IntentLLM 协议，
由 app 层注入真实 DeepSeek 网关；未注入时用确定性启发式回退，保证 Core
可独立测试、离线可用。
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Protocol

from agentos.core.acg.enums import ComplexityLevel
from agentos.core.planning.profile import TaskSemanticProfile


class IntentLLM(Protocol):
    """意图解析所需的最小 LLM 接口。"""

    def generate_json(self, prompt: str, schema: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        ...


_PROFILE_SCHEMA = {
    "type": "object",
    "properties": {
        "primaryGoal": {"type": "string"},
        "keyConstraints": {"type": "array", "items": {"type": "string"}},
        "requiredCapabilities": {"type": "array", "items": {"type": "string"}},
        "estimatedComplexity": {"type": "string", "enum": ["simple", "medium", "complex", "extreme"]},
        "domainHint": {"type": "string"},
        "taskTypeHint": {"type": "string"},
        "implicitRequirements": {"type": "array", "items": {"type": "string"}},
        "riskLevel": {"type": "string"},
    },
    "required": ["primaryGoal", "requiredCapabilities", "estimatedComplexity"],
}

_NON_EXECUTABLE_CAPABILITY_KEYWORDS = (
    "多智能体",
    "协作编排",
    "任务图",
    "图编排",
    "工作流编排",
    "ACG",
    "DAG",
    "低熵通信",
    "上下文组织",
    "字段投递",
    "并行分析",
    "并行处理",
    "输出格式",
)


def _canonical_capability(capability: str) -> Optional[str]:
    raw = (capability or "").strip()
    if not raw:
        return None

    if "报告" in raw and any(k in raw for k in ("生成", "输出", "撰写", "Markdown", "markdown")):
        return "报告生成"
    if ("证据" in raw or "依据" in raw) and any(k in raw for k in ("检索", "匹配", "引用")):
        return "证据检索"
    if "修改" in raw or "修订" in raw:
        return "修改建议"
    if "审核" in raw or "复核" in raw:
        return "人工审核"
    if "条款" in raw and any(k in raw for k in ("分类", "识别", "摘要")):
        return "条款分类"
    if "风险" in raw:
        return "风险识别"
    if any(k in raw for k in ("解析", "提取")) and "合同" in raw:
        return "文本解析"

    compact = raw.replace(" ", "").replace("/", "")
    if any(k.lower() in compact.lower() for k in _NON_EXECUTABLE_CAPABILITY_KEYWORDS):
        return None
    return raw


def _clean_capabilities(capabilities: List[str]) -> List[str]:
    cleaned: List[str] = []
    for capability in capabilities:
        canonical = _canonical_capability(capability)
        if canonical and canonical not in cleaned:
            cleaned.append(canonical)
    return cleaned


def _build_prompt(intent: str, domain: str, task_type: str) -> str:
    return (
        "你是一个任务规划的意图解析器。请将用户需求解析为结构化任务语义画像，"
        "只返回 JSON。字段：primaryGoal（一句核心目标）、keyConstraints（约束列表）、"
        "requiredCapabilities（完成任务所需核心能力，如 文本解析/风险识别/证据检索/报告生成）、"
        "estimatedComplexity（simple/medium/complex/extreme）、domainHint、taskTypeHint、"
        "implicitRequirements（隐含需求）、riskLevel（low/normal/high）。\n\n"
        f"领域提示：{domain}\n任务类型提示：{task_type}\n用户需求：{intent}\n"
    )


class IntentParser:
    """意图解析器。"""

    def __init__(self, llm: Optional[IntentLLM] = None):
        self.llm = llm

    def parse(
        self,
        *,
        intent: str,
        domain: str = "general",
        task_type: str = "general",
    ) -> TaskSemanticProfile:
        if self.llm is not None:
            try:
                return self._parse_with_llm(intent, domain, task_type)
            except Exception:
                # LLM 失败时不阻断规划，回退启发式。
                pass
        return self._heuristic(intent, domain, task_type)

    def _parse_with_llm(self, intent: str, domain: str, task_type: str) -> TaskSemanticProfile:
        result = self.llm.generate_json(_build_prompt(intent, domain, task_type), _PROFILE_SCHEMA)
        data = result.get("data", result) if isinstance(result, dict) else {}
        data.setdefault("domainHint", domain)
        data.setdefault("taskTypeHint", task_type)
        data["rawIntent"] = intent
        return self._enrich_profile(TaskSemanticProfile.model_validate(data), intent, domain, task_type)

    def _heuristic(self, intent: str, domain: str, task_type: str) -> TaskSemanticProfile:
        text = intent or ""
        length = len(text)
        if length > 600:
            complexity = ComplexityLevel.COMPLEX
        elif length > 200:
            complexity = ComplexityLevel.MEDIUM
        else:
            complexity = ComplexityLevel.SIMPLE

        capabilities = self._infer_capabilities(text, domain, task_type)
        risk = "high" if any(k in text for k in ("风险", "合规", "诉讼", "违约")) else "normal"
        profile = TaskSemanticProfile(
            primaryGoal=text[:80] or task_type,
            requiredCapabilities=capabilities,
            estimatedComplexity=complexity,
            domainHint=domain,
            taskTypeHint=task_type,
            riskLevel=risk,
            rawIntent=text,
        )
        return self._enrich_profile(profile, intent, domain, task_type)

    def _enrich_profile(
        self,
        profile: TaskSemanticProfile,
        intent: str,
        domain: str,
        task_type: str,
    ) -> TaskSemanticProfile:
        """用确定性启发式补齐 LLM 可能遗漏的能力，保证图规划稳定。"""
        for cap in self._infer_capabilities(intent or "", domain, task_type, include_defaults=False):
            if cap not in profile.required_capabilities:
                profile.required_capabilities.append(cap)
        profile.required_capabilities = _clean_capabilities(profile.required_capabilities)
        if not profile.domain_hint:
            profile.domain_hint = domain
        if not profile.task_type_hint:
            profile.task_type_hint = task_type
        if not profile.raw_intent:
            profile.raw_intent = intent or ""
        if profile.risk_level in {"", "normal", "low"} and any(k in (intent or "") for k in ("风险", "合规", "诉讼", "违约")):
            profile.risk_level = "high"
        return profile

    @staticmethod
    def _infer_capabilities(text: str, domain: str, task_type: str, *, include_defaults: bool = True) -> List[str]:
        caps: List[str] = []
        keyword_map = {
            "文本解析": ("解析", "提取", "分析", "合同"),
            "条款分类": ("条款", "分类", "付款", "验收", "知识产权", "违约责任"),
            "风险识别": ("风险", "隐患", "合规", "违约"),
            "证据检索": ("证据", "依据", "法规", "检索", "引用"),
            "修改建议": ("建议", "修改", "修订", "优化", "补充"),
            "人工审核": ("人工", "审核", "审批", "复核"),
            "报告生成": ("报告", "总结", "输出", "生成"),
            "代码生成": ("代码", "实现", "函数", "编程"),
            "需求分析": ("需求", "规格", "设计"),
        }
        for cap, keywords in keyword_map.items():
            if any(k in text for k in keywords):
                caps.append(cap)
        if (domain or "").lower() == "legal" and ("合同" in text or "contract" in text.lower()):
            legal_defaults = ["文本解析", "条款分类"]
            if any(k in text for k in ("审查", "风险", "违约", "合规")):
                legal_defaults.extend(["风险识别", "证据检索", "修改建议"])
            if any(k in text for k in ("审查", "报告", "总结", "输出")):
                legal_defaults.append("报告生成")
            for cap in legal_defaults:
                if cap not in caps:
                    caps.append(cap)
        if include_defaults and not caps:
            caps = ["文本解析", "报告生成"]
        return caps


__all__ = ["IntentParser", "IntentLLM", "TaskSemanticProfile"]
