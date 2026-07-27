"""Core-owned bootstrap definition and deterministic native execution capability."""

from __future__ import annotations

from typing import Any

from agentos.agents.base import AgentOutput, AgentProfile, AgentRunContext, BaseAgent
from agentos.core.models.types import WorkflowDefinition, WorkflowDefinitionType


NATIVE_ACG_WORKFLOW_ID = "native_acg_runtime_v1"
NATIVE_AGENT_NAME = "native_general_agent"
NATIVE_CAPABILITIES = (
    "task_understanding",
    "analysis",
    "artifact_generation",
)


class NativeGeneralAgent(BaseAgent):
    """Small offline-safe Agent that executes the native bootstrap capabilities."""

    def __init__(self) -> None:
        super().__init__(
            AgentProfile(
                agentName=NATIVE_AGENT_NAME,
                domain="general",
                capabilities=list(NATIVE_CAPABILITIES),
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
                "verification": {"status": "passed"},
            }
            return AgentOutput(output=output, summary="Task objective understood.")

        if capability == "analysis":
            task_summary = str(upstream.get("task_summary") or objective)
            output = {
                "analysis": f"围绕“{task_summary}”形成目标、执行阶段、主要风险和交付物分析。",
                "verification": {"status": "passed"},
            }
            return AgentOutput(output=output, summary="Task analysis completed.")

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
