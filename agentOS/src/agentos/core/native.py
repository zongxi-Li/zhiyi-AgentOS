"""Core-owned bootstrap definition and deterministic native execution capability."""

from __future__ import annotations

from typing import Any

from agentos.agents.base import AgentOutput, AgentProfile, AgentRunContext, BaseAgent
from agentos.core.models.types import WorkflowDefinition, WorkflowDefinitionType
from agentos.core.planning.native_capabilities import NATIVE_CAPABILITY_IDS


NATIVE_ACG_WORKFLOW_ID = "native_acg_runtime_v1"
NATIVE_AGENT_NAME = "native_general_agent"
# Backward-compatible export derived from the native Catalog contribution.
NATIVE_CAPABILITIES = NATIVE_CAPABILITY_IDS


class NativeGeneralAgent(BaseAgent):
    """Small offline-safe Agent that executes the native bootstrap capabilities."""

    def __init__(self) -> None:
        super().__init__(
            AgentProfile(
                agentName=NATIVE_AGENT_NAME,
                domain="general",
                capabilities=list(NATIVE_CAPABILITY_IDS),
                allowedTools=[
                    "knowledge_search",
                    "current_datetime",
                ],
                description="Executes domain-neutral understanding, analysis, and artifact delivery.",
            )
        )

    async def run(self, context: AgentRunContext) -> AgentOutput:
        objective = str(
            context.task.input.get("userIntent")
            or context.task.input.get("intent")
            or context.task.title
        ).strip()
        upstream = self._upstream_data(context)
        capability = (context.step.capability or "").strip()

        if capability == "task_understanding":
            output = {
                "task_summary": objective,
                "constraints": [],
                "verification": {"status": "passed"},
            }
            return AgentOutput(output=output, summary="Task objective understood.")

        task_summary = str(upstream.get("task_summary") or objective)
        if capability == "information_retrieval":
            if context.tool_runtime is None:
                raise RuntimeError("read-only tool runtime is not configured")
            result = await context.tool_runtime.run(
                f"Research this objective and return a concise evidence-backed result: {task_summary}",
                require_evidence=True,
            )
            sources = [item.public_dict() for item in result.sources]
            evidence_refs = [item.citation_id for item in result.sources]
            if not evidence_refs:
                raise RuntimeError("information_retrieval requires evidence but no source was returned")
            return AgentOutput(
                output={
                    "retrieved_information": [result.text],
                    "sources": sources,
                    "evidence_refs": evidence_refs,
                },
                summary=f"Retrieved {len(evidence_refs)} evidence source(s).",
                sources=sources,
                toolExecutions=[item.public_dict() for item in result.tool_executions],
                evidenceRefs=evidence_refs,
            )
        if capability == "evidence_analysis" and not upstream.get("evidence_refs"):
            raise RuntimeError("evidence_analysis requires upstream evidence references")
        outputs = {
            "information_extraction": {
                "extracted_information": {"summary": task_summary, "items": []},
            },
            "requirement_analysis": {
                "requirements": ["明确目标范围", "定义质量标准", "形成可验收交付物"],
                "acceptance_criteria": ["目标覆盖", "过程可执行", "结果可验证"],
            },
            "process_decomposition": {
                "process_steps": ["准备", "执行", "质量检查", "交付"],
            },
            "resource_planning": {
                "resource_plan": ["人员", "设备", "信息与时间"],
                "capacity_plan": "按阶段负载进行资源配置",
            },
            "architecture_design": {
                "architecture": "分层、模块化并保留清晰接口的通用架构",
                "components": ["接入层", "能力层", "数据层", "治理层"],
                "data_flow": "输入 → 处理 → 验证 → 交付",
            },
            "analysis": {
                "analysis": f"围绕“{task_summary}”分析目标、约束、执行路径和交付标准。",
            },
            "comparative_analysis": {
                "comparison": "按适用性、成本、风险和可验证性比较候选方案",
                "alternatives": ["渐进方案", "集中方案"],
            },
            "evidence_analysis": {
                "evidence_analysis": "已按相关性、可信度和覆盖范围整理证据线索",
                "evidence_refs": upstream.get("evidence_refs") or [],
            },
            "cost_analysis": {
                "cost_analysis": "成本由资源投入、实施周期和质量保障活动构成",
                "cost_drivers": ["资源", "周期", "质量"],
            },
            "risk_analysis": {
                "risk_analysis": "关注范围、依赖、进度、质量与安全风险",
                "risks": ["范围偏移", "关键依赖延迟", "质量验证不足"],
            },
            "solution_design": {
                "solution_design": "采用分阶段实施、阶段验证和持续风险控制的方案",
            },
            "verification": {
                "verification": {"status": "passed", "criteria": "目标、过程和交付物可核验"},
            },
        }
        if capability in outputs:
            return AgentOutput(output=outputs[capability], summary=f"{capability} completed.")

        analysis = str(upstream.get("analysis") or f"已分析任务：{objective}")
        deliverable = (
            f"# 任务实施方案\n\n"
            f"## 目标\n{objective}\n\n"
            f"## 分析\n{analysis}\n\n"
            "## 执行阶段\n1. 明确范围与验收标准\n2. 分阶段实施并验证\n3. 汇总交付物并复盘\n\n"
            "## 风险控制\n持续检查范围、质量、进度和依赖风险。\n\n"
            "## 交付物\n实施计划、阶段成果、验证记录和最终总结。"
        )
        output = {
            "deliverable": deliverable,
            "final_answer": deliverable,
            "verification": {"status": "passed"},
        }
        return AgentOutput(output=output, summary="Generic artifact generated.")

    @staticmethod
    def _upstream_data(context: AgentRunContext) -> dict[str, Any]:
        pack = context.context_pack
        data = getattr(pack, "data", None) if pack is not None else None
        return dict(data) if isinstance(data, dict) else {}


def native_bootstrap_definition() -> WorkflowDefinition:
    """Return the empty ACG definition that enters the existing PlanningEngine."""

    return WorkflowDefinition(
        workflowId=NATIVE_ACG_WORKFLOW_ID,
        name="知弈OS原生 ACG 运行时",
        domain="general",
        intent="general",
        runtimeEngine="acg",
        definitionType=WorkflowDefinitionType.NATIVE_BOOTSTRAP,
        description="Core-owned planner bootstrap for native domain-neutral tasks.",
        steps=[],
    )


def register_native_runtime(*, agent_registry, workflow_registry) -> None:
    """Register Core definitions before any application Pack is discovered."""

    agent_registry.register(NativeGeneralAgent())
    workflow_registry.register(native_bootstrap_definition())


__all__ = [
    "NATIVE_ACG_WORKFLOW_ID",
    "NATIVE_AGENT_NAME",
    "NATIVE_CAPABILITIES",
    "NativeGeneralAgent",
    "native_bootstrap_definition",
    "register_native_runtime",
]
