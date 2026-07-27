"""Core-owned, bounded capability contribution for native domain-neutral tasks."""

from __future__ import annotations

from agentos.core.planning.capabilities import CapabilityCatalog, PlanningCapabilityDescriptor


def _schema(*required: str) -> dict:
    return {"type": "object", "required": list(required)}


def native_capability_descriptors() -> tuple[PlanningCapabilityDescriptor, ...]:
    general = ["general"]
    return (
        PlanningCapabilityDescriptor(
            capabilityId="task_understanding", displayName="任务理解",
            aliases=["理解任务", "任务目标", "目标", "约束"], planningStage="understand",
            outputContract=_schema("task_summary", "constraints"), parallelizable=False,
            domainHints=general, priority=10,
        ),
        PlanningCapabilityDescriptor(
            capabilityId="information_extraction", displayName="信息提取",
            aliases=["信息提取", "抽取", "要素梳理"], planningStage="decompose",
            dependsOn=["task_understanding"], inputContract=_schema("task_summary"),
            outputContract=_schema("extracted_information"), domainHints=general, priority=20,
        ),
        PlanningCapabilityDescriptor(
            capabilityId="information_retrieval", displayName="资料检索",
            aliases=["资料梳理", "资料检索", "信息检索", "调研", "文献"], planningStage="decompose",
            dependsOn=["task_understanding"], inputContract=_schema("task_summary"),
            outputContract=_schema("retrieved_information", "evidence_refs"),
            requiresEvidence=True, domainHints=general, priority=21,
        ),
        PlanningCapabilityDescriptor(
            capabilityId="requirement_analysis", displayName="需求分析",
            aliases=["需求", "需求分析", "验收条件", "功能要求"], planningStage="decompose",
            dependsOn=["task_understanding"], inputContract=_schema("task_summary"),
            outputContract=_schema("requirements", "acceptance_criteria"),
            writesMemory=True, domainHints=general, priority=22,
        ),
        PlanningCapabilityDescriptor(
            capabilityId="process_decomposition", displayName="流程拆解",
            aliases=["工序", "流程拆解", "流程规划", "步骤拆解", "生产流程"], planningStage="decompose",
            dependsOn=["task_understanding"], inputContract=_schema("task_summary"),
            outputContract=_schema("process_steps"), writesMemory=True,
            domainHints=general, priority=23,
        ),
        PlanningCapabilityDescriptor(
            capabilityId="resource_planning", displayName="资源规划",
            aliases=["资源", "设备资源", "人员配置", "产能"], planningStage="analyze",
            dependsOn=["process_decomposition"], inputContract=_schema("process_steps"),
            outputContract=_schema("resource_plan", "capacity_plan"),
            domainHints=general, priority=30,
        ),
        PlanningCapabilityDescriptor(
            capabilityId="architecture_design", displayName="架构设计",
            aliases=["系统架构", "技术架构", "架构设计", "组件", "接口", "数据流"],
            planningStage="analyze", dependsOn=["requirement_analysis"],
            inputContract=_schema("requirements"),
            outputContract=_schema("architecture", "components", "data_flow"),
            writesMemory=True, domainHints=general, priority=31,
        ),
        PlanningCapabilityDescriptor(
            capabilityId="analysis", displayName="通用分析",
            aliases=["分析", "评估"], planningStage="analyze",
            dependsOn=["task_understanding"], inputContract=_schema("task_summary"),
            outputContract=_schema("analysis"), domainHints=general, priority=32,
        ),
        PlanningCapabilityDescriptor(
            capabilityId="evidence_analysis", displayName="证据分析",
            aliases=["证据分析", "依据分析", "资料分析"], planningStage="analyze",
            dependsOn=["information_retrieval"], inputContract=_schema("retrieved_information"),
            outputContract=_schema("evidence_analysis", "evidence_refs"),
            requiresEvidence=True, writesMemory=True, domainHints=general, priority=33,
        ),
        PlanningCapabilityDescriptor(
            capabilityId="comparative_analysis", displayName="比较分析",
            aliases=["方案比较", "对比分析", "比较", "备选方案"], planningStage="analyze",
            dependsOn=["evidence_analysis"], inputContract=_schema("evidence_analysis"),
            outputContract=_schema("comparison", "alternatives"),
            domainHints=general, priority=34,
        ),
        PlanningCapabilityDescriptor(
            capabilityId="cost_analysis", displayName="成本分析",
            aliases=["成本", "预算", "费用"], planningStage="analyze",
            dependsOn=["process_decomposition"], inputContract=_schema("process_steps"),
            outputContract=_schema("cost_analysis", "cost_drivers"),
            domainHints=general, priority=35,
        ),
        PlanningCapabilityDescriptor(
            capabilityId="risk_analysis", displayName="风险分析",
            aliases=["风险", "安全风险", "风险分析", "风险控制"], planningStage="analyze",
            dependsOn=["task_understanding"],
            optionalDependencies=["requirement_analysis", "process_decomposition", "architecture_design"],
            inputContract=_schema("task_summary"), outputContract=_schema("risk_analysis", "risks"),
            writesMemory=True, domainHints=general, priority=36,
        ),
        PlanningCapabilityDescriptor(
            capabilityId="solution_design", displayName="方案设计",
            aliases=["解决方案", "方案设计", "实施方案"], planningStage="synthesize",
            dependsOn=["analysis"], optionalDependencies=["requirement_analysis", "process_decomposition", "architecture_design"],
            inputContract=_schema("analysis"), outputContract=_schema("solution_design"),
            producesArtifact=True, writesMemory=True, domainHints=general, priority=40,
        ),
        PlanningCapabilityDescriptor(
            capabilityId="verification", displayName="验证",
            aliases=["验证", "验收", "质量控制", "结论验证", "测试方式"], planningStage="verify",
            dependsOn=["task_understanding"],
            optionalDependencies=["requirement_analysis", "process_decomposition", "resource_planning", "architecture_design", "analysis", "comparative_analysis", "evidence_analysis", "cost_analysis", "risk_analysis", "solution_design"],
            inputContract=_schema("task_summary"), outputContract=_schema("verification"),
            parallelizable=False, domainHints=general, priority=50,
        ),
        PlanningCapabilityDescriptor(
            capabilityId="artifact_generation", displayName="成果生成",
            aliases=["报告", "方案", "交付物", "文档"], planningStage="deliver",
            dependsOn=["task_understanding"],
            optionalDependencies=["information_extraction", "information_retrieval", "requirement_analysis", "process_decomposition", "resource_planning", "architecture_design", "analysis", "comparative_analysis", "evidence_analysis", "cost_analysis", "risk_analysis", "solution_design", "verification"],
            inputContract=_schema("task_summary"),
            outputContract=_schema("deliverable", "final_answer", "verification"),
            producesArtifact=True, writesMemory=True, parallelizable=False,
            domainHints=general, priority=60,
        ),
    )


NATIVE_CAPABILITY_IDS = tuple(
    descriptor.capability_id for descriptor in native_capability_descriptors()
)


def register_native_capabilities(catalog: CapabilityCatalog) -> None:
    for descriptor in native_capability_descriptors():
        catalog.register(descriptor)


__all__ = ["NATIVE_CAPABILITY_IDS", "native_capability_descriptors", "register_native_capabilities"]
