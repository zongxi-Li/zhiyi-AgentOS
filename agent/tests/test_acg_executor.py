"""ACG 执行器（就绪集并行调度）端到端测试。

验证 Core Native 自研 ACG 引擎：
- 线性工作流经 runtime_engine=acg 执行，行为与线性一致；
- 并行分支：菱形 ACG 中两个无依赖 step 并发执行；
- 人审中断 + approve 续跑；
- 节点级统一 Trace（step_started/agent_called/step_succeeded）。
"""

from __future__ import annotations

import asyncio

import pytest

from agentos.agents import AgentRegistry
from agentos.agents.base import AgentOutput, AgentProfile, BaseAgent
from agentos.core.acg import ACGBlueprint, ACGEdge, EdgeType, StepNode
from agentos.core.models.types import (
    ReviewDecision,
    ReviewDecisionType,
    StepStatus,
    TraceEventType,
    WorkflowDefinition,
    WorkflowStatus,
    WorkflowStepDefinition,
)
from agentos.core.runtime import WorkflowRuntime
from agentos.core.workflow.registry import WorkflowRegistry


class _Agent(BaseAgent):
    def __init__(self, name, calls):
        super().__init__(AgentProfile(agentName=name, domain="test", capabilities=[name]))
        self.calls = calls

    async def run(self, context):
        self.calls.append(context.step.step_id)
        return AgentOutput(
            output={"agent": self.profile.agent_name, "step": context.step.step_id},
            summary=f"{self.profile.agent_name} done",
        )


def _runtime(steps, agent_names, *, engine="acg"):
    registry = AgentRegistry()
    calls: list[str] = []
    for name in agent_names:
        registry.register(_Agent(name, calls))
    wf_registry = WorkflowRegistry()
    wf_registry.register(
        WorkflowDefinition(
            workflowId="acg_wf",
            name="ACG WF",
            domain="test",
            intent="demo",
            runtimeEngine=engine,
            steps=steps,
        )
    )
    runtime = WorkflowRuntime(agent_registry=registry, workflow_registry=wf_registry)
    return runtime, calls


def test_acg_engine_runs_linear_workflow():
    async def _run():
        steps = [
            WorkflowStepDefinition(stepId="a", name="A", agentName="a", nextStepId="b"),
            WorkflowStepDefinition(stepId="b", name="B", agentName="b", nextStepId="c"),
            WorkflowStepDefinition(stepId="c", name="C", agentName="c"),
        ]
        runtime, calls = _runtime(steps, ["a", "b", "c"])
        task = runtime.create_task(title="t", domain="test", intent="demo", input={})
        run = await runtime.start(task.task_id, workflow_id="acg_wf")

        assert run.status == WorkflowStatus.COMPLETED
        assert calls == ["a", "b", "c"]
        assert run.runtime_engine == "acg"
        assert run.acg_blueprint is not None
        assert set(run.completed_step_ids) == {"a", "b", "c"}

    asyncio.run(_run())


def test_acg_engine_parallel_branch_executes_both():
    """注入菱形 ACG：a -> {b, c} -> d，验证 b、c 并行执行、d 在二者后。"""

    async def _run():
        steps = [
            WorkflowStepDefinition(stepId="a", name="A", agentName="a", nextStepId="d"),
            WorkflowStepDefinition(stepId="b", name="B", agentName="b"),
            WorkflowStepDefinition(stepId="c", name="C", agentName="c"),
            WorkflowStepDefinition(stepId="d", name="D", agentName="d"),
        ]
        runtime, calls = _runtime(steps, ["a", "b", "c", "d"])

        blueprint = ACGBlueprint(objective="diamond")
        for nid in ["a", "b", "c", "d"]:
            blueprint.nodes.append(StepNode(nodeId=nid, name=nid.upper(), agentName=nid))
        blueprint.edges += [
            ACGEdge(sourceId="a", targetId="b", edgeType=EdgeType.DEPENDENCY),
            ACGEdge(sourceId="a", targetId="c", edgeType=EdgeType.DEPENDENCY),
            ACGEdge(sourceId="b", targetId="d", edgeType=EdgeType.DEPENDENCY),
            ACGEdge(sourceId="c", targetId="d", edgeType=EdgeType.DEPENDENCY),
        ]

        task = runtime.create_task(
            title="t",
            domain="test",
            intent="demo",
            input={"acgBlueprint": blueprint.model_dump(by_alias=True, mode="json")},
        )
        run = await runtime.start(task.task_id, workflow_id="acg_wf")

        assert run.status == WorkflowStatus.COMPLETED
        assert set(calls) == {"a", "b", "c", "d"}
        # a 最先、d 最后；b、c 在中间（并行，顺序不固定）
        assert calls[0] == "a"
        assert calls[-1] == "d"
        assert set(calls[1:3]) == {"b", "c"}

    asyncio.run(_run())


def test_acg_engine_human_review_interrupt_and_resume():
    async def _run():
        steps = [
            WorkflowStepDefinition(stepId="a", name="A", agentName="a", nextStepId="gate"),
            WorkflowStepDefinition(stepId="gate", name="Gate", agentName="gate", reviewRequired=True, nextStepId="z"),
            WorkflowStepDefinition(stepId="z", name="Z", agentName="z"),
        ]
        runtime, calls = _runtime(steps, ["a", "gate", "z"])
        task = runtime.create_task(title="t", domain="test", intent="demo", input={})
        run = await runtime.start(task.task_id, workflow_id="acg_wf", review_mode="human_in_loop")

        assert run.status == WorkflowStatus.WAITING_REVIEW
        assert "z" not in calls  # 报告步骤尚未执行

        resumed = await runtime.apply_review(
            ReviewDecision(runId=run.run_id, stepId="gate", decision=ReviewDecisionType.APPROVED)
        )
        assert resumed.status == WorkflowStatus.COMPLETED
        assert "z" in calls

    asyncio.run(_run())


def test_acg_engine_emits_unified_step_trace():
    async def _run():
        steps = [WorkflowStepDefinition(stepId="a", name="A", agentName="a")]
        runtime, _ = _runtime(steps, ["a"])
        task = runtime.create_task(title="t", domain="test", intent="demo", input={})
        run = await runtime.start(task.task_id, workflow_id="acg_wf")

        event_types = {e.event_type for e in run.trace}
        assert TraceEventType.STEP_SCHEDULED in event_types
        assert TraceEventType.STEP_STARTED in event_types
        assert TraceEventType.AGENT_CALLED in event_types
        assert TraceEventType.STEP_SUCCEEDED in event_types
        # 摘要字段存在
        succeeded = [e for e in run.trace if e.event_type == TraceEventType.STEP_SUCCEEDED][0]
        assert "outputSummary" in succeeded.payload

    asyncio.run(_run())


def test_acg_engine_emits_low_entropy_provenance_events():
    """多步工作流应产生数据生产/消费事件，并在装配时携带节省率度量。"""

    async def _run():
        steps = [
            WorkflowStepDefinition(stepId="a", name="A", agentName="a", nextStepId="b"),
            WorkflowStepDefinition(stepId="b", name="B", agentName="b"),
        ]
        runtime, _ = _runtime(steps, ["a", "b"])
        task = runtime.create_task(title="t", domain="test", intent="demo", input={})
        run = await runtime.start(task.task_id, workflow_id="acg_wf")

        event_types = {e.event_type for e in run.trace}
        assert TraceEventType.DATA_PRODUCED in event_types
        assert TraceEventType.DATA_CONSUMED in event_types

        consumed = [e for e in run.trace if e.event_type == TraceEventType.DATA_CONSUMED]
        assert consumed, "下游 b 应有数据消费事件"
        payload = consumed[0].payload
        assert "savingRatio" in payload
        assert "tokensDelivered" in payload
        assert payload["sourceStepIds"] == ["a"]

    asyncio.run(_run())


def test_acg_engine_planner_driven_static_template():
    """usePlanner=true 时，规划器命中静态模板并经 ACG 引擎执行全链路。"""

    class _LegalAgent(BaseAgent):
        def __init__(self, name, calls):
            super().__init__(AgentProfile(agentName=name, domain="legal", capabilities=[name]))
            self.calls = calls

        async def run(self, context):
            self.calls.append(context.step.step_id)
            return AgentOutput(output={"step": context.step.step_id}, summary="ok")

    async def _run():
        steps = [
            WorkflowStepDefinition(stepId="parse", name="解析", agentName="parse", nextStepId="risk"),
            WorkflowStepDefinition(stepId="risk", name="风险", agentName="risk"),
        ]
        registry = AgentRegistry()
        calls: list[str] = []
        for name in ["parse", "risk"]:
            registry.register(_LegalAgent(name, calls))
        wf_registry = WorkflowRegistry()
        wf_registry.register(
            WorkflowDefinition(
                workflowId="acg_wf",
                name="合同审查",
                domain="legal",
                intent="contract_review",
                description="解析合同并识别风险",
                runtimeEngine="acg",
                steps=steps,
            )
        )
        runtime = WorkflowRuntime(agent_registry=registry, workflow_registry=wf_registry)
        task = runtime.create_task(
            title="审查合同",
            domain="legal",
            intent="contract_review",
            input={"usePlanner": True, "userIntent": "审查这份采购合同的违约风险"},
        )
        run = await runtime.start(task.task_id, workflow_id="acg_wf")

        assert run.status == WorkflowStatus.COMPLETED
        assert calls == ["parse", "risk"]
        # 规划决策应入 trace
        planner_events = [
            e for e in run.trace
            if e.event_type == TraceEventType.TASK_STATUS_CHANGED and "Planner" in e.observation
        ]
        assert planner_events
        assert planner_events[0].payload["strategy"] == "static_template"

    asyncio.run(_run())
