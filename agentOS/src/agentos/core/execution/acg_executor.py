"""ACG 执行器：基于就绪集的并行 Step 调度引擎（Core Native 自研）。

把执行模型从“线性 nextStepId 单指针”升级为“按 DEPENDENCY 边计算就绪集，
并行驱动多个无依赖 Step”。这是动态异构拓扑“可见性”的核心：执行顺序由
图结构决定，而非预设链表，支持并行分支、条件分支与汇聚。

设计要点：
- 复用既有 Orchestrator.dispatch_agent / AgentRegistry / WorkflowMemory，
  每个 StepNode 仍映射到 run.steps 里的一个 WorkflowStep，从而无缝复用
  现有 Pack 智能体、Trace、Checkpoint 与前端展示。
- 与线性 _run_until_blocked 并存，作为 runtime_engine="acg" 的新执行路径，
  不影响 native 既有行为。
- 节点级统一 Trace（step_started/agent_called/step_succeeded/step_failed）。
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Dict, List, Optional, Set

from agentos.core.acg import (
    ACGBlueprint,
    ControlNode,
    ControlType,
    EdgeType,
    NodeType,
    StepNode,
    ready_steps,
    validate_blueprint,
)
from agentos.core.communication import ContextAssembler, ProvenanceLedger
from agentos.core.execution.fault_injection import FaultInjector, InjectedFault
from agentos.core.execution.step_wrapper import (
    StepExecutionTimer,
    input_summary,
    output_summary,
)
from agentos.core.models.types import (
    AgentTask,
    StepStatus,
    TraceEventType,
    WorkflowRun,
    WorkflowStatus,
    WorkflowStep,
    utc_now,
)
from agentos.memory.workflow_memory import WorkflowMemory

if TYPE_CHECKING:
    from agentos.core.runtime import WorkflowRuntime


class ACGExecutor:
    """就绪集并行调度执行器。"""

    def __init__(self, runtime: "WorkflowRuntime", *, max_parallelism: int = 4):
        self.runtime = runtime
        self.max_parallelism = max(1, max_parallelism)
        self.ledger = ProvenanceLedger()
        self.assembler = ContextAssembler(self.ledger)
        self.fault_injector = FaultInjector()

    # ------------------------------------------------------------------
    # 入口
    # ------------------------------------------------------------------
    async def run(
        self,
        *,
        task: AgentTask,
        run: WorkflowRun,
        workflow,
        blueprint: ACGBlueprint,
    ) -> WorkflowRun:
        validate_blueprint(blueprint)
        run.acg_blueprint = blueprint.model_dump(by_alias=True, mode="json")
        self.fault_injector = FaultInjector.from_config(task.input.get("faultInjection"))
        if self.fault_injector.active:
            self.runtime.trace_store.append(
                run=run,
                event_type=TraceEventType.RUN_STARTED,
                observation=(
                    f"Fault injection armed: {self.fault_injector.fault_type.value} "
                    f"at {self.fault_injector.step_id}"
                ),
                payload={
                    "faultType": self.fault_injector.fault_type.value,
                    "stepId": self.fault_injector.step_id,
                    "maxTriggers": self.fault_injector.max_triggers,
                },
            )
        self.runtime.trace_store.append(
            run=run,
            event_type=TraceEventType.RUN_STARTED,
            observation=f"ACG execution started: {blueprint.graph_id}",
            payload={
                "graphId": blueprint.graph_id,
                "nodeCount": blueprint.node_count,
                "edgeCount": blueprint.edge_count,
                "engine": "acg",
            },
        )
        self.runtime.workflow_store.save_run(run)
        return await self._drive(task=task, run=run, workflow=workflow, blueprint=blueprint)

    async def resume(
        self,
        *,
        task: AgentTask,
        run: WorkflowRun,
        workflow,
        blueprint: ACGBlueprint,
    ) -> WorkflowRun:
        """人审/检查点之后从当前完成集续跑就绪集，不重置 RUN_STARTED。"""
        return await self._drive(task=task, run=run, workflow=workflow, blueprint=blueprint)

    # ------------------------------------------------------------------
    # 主调度循环：每轮计算就绪集 → 并行执行 → 更新完成集
    # ------------------------------------------------------------------
    async def _drive(self, *, task, run, workflow, blueprint: ACGBlueprint) -> WorkflowRun:
        self.runtime._transition_run(run, WorkflowStatus.RUNNING)
        self.runtime.task_manager.mark_running(task)
        completed: Set[str] = set(run.completed_step_ids)

        while True:
            # 1) 先处理已就绪的控制节点（分支/汇聚/起止），可能改变可达性
            self._resolve_control_nodes(blueprint, completed)

            ready = self._eligible_steps(blueprint, run, completed)
            if not ready:
                if self._all_steps_done(blueprint, completed, run):
                    self.runtime._complete_run(task, run)
                    self.runtime.workflow_store.save_run(run)
                    return run
                # 没有就绪步骤但也未全完成：可能在等待人审，直接返回当前态
                self.runtime.workflow_store.save_run(run)
                return run

            # 2) 调度本批就绪集（受并行上限约束）
            batch = ready[: self.max_parallelism]
            for node_id in batch:
                self.runtime.trace_store.append(
                    run=run,
                    event_type=TraceEventType.STEP_SCHEDULED,
                    step_id=node_id,
                    observation=f"Step scheduled (ready set size={len(ready)})",
                    payload={"readySet": ready, "batch": batch},
                )
            self.runtime.workflow_store.save_run(run)

            results = await asyncio.gather(
                *[
                    self._execute_step(task=task, run=run, workflow=workflow, blueprint=blueprint, node_id=nid)
                    for nid in batch
                ],
                return_exceptions=True,
            )

            # 3) 结算本批结果
            waiting_review = False
            self_healed = False
            for node_id, outcome in zip(batch, results):
                if isinstance(outcome, InjectedFault):
                    # 可恢复故障：检查点 + 局部重规划，自愈续跑（不置 run 失败）
                    if self._self_heal(run, task, blueprint, node_id, outcome):
                        self_healed = True
                        continue
                    self._mark_step_failed(run, task, node_id, outcome)
                    self.runtime.workflow_store.save_run(run)
                    return run
                if isinstance(outcome, Exception):
                    self._mark_step_failed(run, task, node_id, outcome)
                    self.runtime.workflow_store.save_run(run)
                    return run
                status = outcome
                if status == StepStatus.WAITING_REVIEW:
                    waiting_review = True
                elif status == StepStatus.COMPLETED:
                    completed.add(node_id)

            run.completed_step_ids = sorted(completed)
            run.provenance = self.ledger.to_graph()
            run.output = self.runtime.orchestrator.compose_final_output(run)
            run.updated_at = utc_now()
            self.runtime.workflow_store.save_run(run)

            if waiting_review:
                # 命中人审中断：保持 waiting_review，等待 apply_review 续跑
                return run

    # ------------------------------------------------------------------
    # 就绪集过滤：排除已 RUNNING / WAITING_REVIEW / 已完成的节点
    # ------------------------------------------------------------------
    def _eligible_steps(self, blueprint: ACGBlueprint, run: WorkflowRun, completed: Set[str]) -> List[str]:
        candidates = ready_steps(blueprint, completed)
        eligible: List[str] = []
        for node_id in candidates:
            step = self._bridge_step(run, blueprint, node_id)
            if step.status in {StepStatus.PENDING, StepStatus.RETRYING}:
                eligible.append(node_id)
        return eligible

    def _all_steps_done(self, blueprint: ACGBlueprint, completed: Set[str], run: WorkflowRun) -> bool:
        for step_node in blueprint.step_nodes():
            if step_node.node_id not in completed:
                bridged = self._bridge_step(run, blueprint, step_node.node_id)
                if bridged.status != StepStatus.WAITING_REVIEW:
                    return False
        return True

    # ------------------------------------------------------------------
    # StepNode ↔ WorkflowStep 桥接：复用既有 run.steps / agent dispatch
    # ------------------------------------------------------------------
    def _bridge_step(self, run: WorkflowRun, blueprint: ACGBlueprint, node_id: str) -> WorkflowStep:
        """返回 run.steps 中对应该 StepNode 的 WorkflowStep；缺失则按节点定义补建。"""
        try:
            return run.get_step(node_id)
        except KeyError:
            node = blueprint.get_node(node_id)
            assert isinstance(node, StepNode)
            step = WorkflowStep(
                stepId=node.node_id,
                name=node.name or node.node_id,
                agentName=node.agent_name or node.node_id,
                capability=node.capability,
                input=dict(node.input_spec),
                reviewRequired=node.review_required,
                maxRetries=node.retry_limit,
            )
            run.steps.append(step)
            return step

    def _data_sources(self, blueprint: ACGBlueprint, node_id: str) -> List[str]:
        """优先按 COMMUNICATION 边取真实数据生产者，兼容旧图的 DEPENDENCY 边。"""
        source_ids = [edge.source_id for edge in blueprint.incoming(node_id, EdgeType.COMMUNICATION)]
        if not source_ids:
            source_ids = blueprint.dependency_sources(node_id)
        seen: set[str] = set()
        ordered: List[str] = []
        for source_id in source_ids:
            if source_id in seen:
                continue
            seen.add(source_id)
            ordered.append(source_id)
        return ordered

    # ------------------------------------------------------------------
    # 单节点执行：统一 Trace wrapper（started → agent_called/succeeded → failed）
    # ------------------------------------------------------------------
    async def _execute_step(
        self, *, task, run: WorkflowRun, workflow, blueprint: ACGBlueprint, node_id: str
    ) -> StepStatus:
        step = self._bridge_step(run, blueprint, node_id)
        self.runtime._transition_step(step, StepStatus.RUNNING)
        run.current_step_id = node_id
        run.updated_at = utc_now()
        self.runtime.trace_store.append(
            run=run,
            event_type=TraceEventType.STEP_STARTED,
            step_id=node_id,
            agent_name=step.agent_name,
            observation=f"Step started: {step.name}",
            payload={"inputSummary": input_summary(step.input)},
        )

        # 低熵通信：按 input_spec 精准装配下游上下文，记录消费血缘与节省率。
        step_node = blueprint.get_node(node_id)
        upstream_outputs = {
            sid: dict(run.get_step(sid).output)
            for sid in self._data_sources(blueprint, node_id)
            if self._safe_has_step(run, sid)
        }
        if isinstance(step_node, StepNode) and upstream_outputs:
            pack = self.assembler.assemble(
                run_id=run.run_id,
                blueprint=blueprint,
                step_node=step_node,
                objective=blueprint.objective,
                upstream_outputs=upstream_outputs,
            )
            self.runtime.trace_store.append(
                run=run,
                event_type=TraceEventType.DATA_CONSUMED,
                step_id=node_id,
                agent_name=step.agent_name,
                observation=(
                    f"Context assembled: {pack.tokens_delivered}/{pack.tokens_available} tokens "
                    f"(saved {pack.saving_ratio:.1%})"
                ),
                payload={
                    "sourceStepIds": pack.source_step_ids,
                    "tokensDelivered": pack.tokens_delivered,
                    "tokensAvailable": pack.tokens_available,
                    "savingRatio": pack.saving_ratio,
                    "evidenceRefs": pack.evidence_refs,
                },
            )

        memory = WorkflowMemory.from_run(run)
        timer = StepExecutionTimer()
        # 故障注入点：在真正调用 Agent 前触发（模拟模型超时/Agent崩溃等）。
        self.fault_injector.fire(node_id)
        result, _ = await self.runtime.orchestrator.dispatch_agent(
            task=task, run=run, workflow=workflow, step=step, memory=memory
        )
        duration_ms = timer.elapsed_ms()

        step.output = dict(result.output)
        # 数据生产事件：登记产物，供前向追溯与节省率统计。
        self.assembler.record_production(node_id, step.output)
        self.runtime.trace_store.append(
            run=run,
            event_type=TraceEventType.DATA_PRODUCED,
            step_id=node_id,
            agent_name=step.agent_name,
            observation=f"Data produced by {node_id}",
            payload={"fields": sorted(step.output.keys())},
        )
        self.runtime.trace_store.append(
            run=run,
            event_type=TraceEventType.AGENT_CALLED,
            step_id=node_id,
            agent_name=step.agent_name,
            observation=result.summary or f"Agent completed: {step.agent_name}",
            payload=step.output,
            duration_ms=duration_ms,
        )

        # 人审中断：保持 waiting_review，建检查点，等待 apply_review
        if step.requires_review and run.review_mode != "auto":
            self.runtime._transition_step(step, StepStatus.WAITING_REVIEW)
            self.runtime._transition_run(run, WorkflowStatus.WAITING_REVIEW)
            run.current_step_id = node_id
            self.runtime.task_manager.mark_waiting_review(task)
            self.runtime._create_checkpoint(run, step)
            self.runtime.trace_store.append(
                run=run,
                event_type=TraceEventType.REVIEW_REQUIRED,
                step_id=node_id,
                agent_name=step.agent_name,
                observation=f"Review required for step: {node_id}",
                payload=step.output,
            )
            return StepStatus.WAITING_REVIEW

        self.runtime._transition_step(step, StepStatus.COMPLETED)
        self.runtime.trace_store.append(
            run=run,
            event_type=TraceEventType.STEP_SUCCEEDED,
            step_id=node_id,
            agent_name=step.agent_name,
            observation=f"Step succeeded: {step.name}",
            payload={"outputSummary": output_summary(step.output)},
            duration_ms=duration_ms,
        )
        self.runtime._create_checkpoint(run, step)
        return StepStatus.COMPLETED

    # ------------------------------------------------------------------
    # 控制节点处理：把已满足前置的 Control 节点并入完成集，激活其分支
    # ------------------------------------------------------------------
    def _resolve_control_nodes(self, blueprint: ACGBlueprint, completed: Set[str]) -> None:
        """处理 START/PARALLEL/CONSENSUS 等无副作用控制节点。

        当前阶段：依赖已满足的控制节点直接并入完成集，使其下游 DEPENDENCY
        目标变为可达（PARALLEL 扇出、CONSENSUS 汇聚天然由就绪集语义实现）。
        IF/LOOP 的条件求值留待后续阶段（需运行时数据），此处仅放行无条件控制节点。
        """
        for node in blueprint.nodes_of_type(NodeType.CONTROL):
            if node.node_id in completed:
                continue
            assert isinstance(node, ControlNode)
            if node.control_type in {ControlType.START, ControlType.PARALLEL, ControlType.CONSENSUS, ControlType.END}:
                deps = blueprint.dependency_sources(node.node_id)
                if all(dep in completed for dep in deps):
                    completed.add(node.node_id)

    # ------------------------------------------------------------------
    # 失败标记：复用 runtime 的重试/失败状态流转
    # ------------------------------------------------------------------
    def _mark_step_failed(self, run: WorkflowRun, task, node_id: str, exc: Exception) -> None:
        try:
            step = run.get_step(node_id)
        except KeyError:
            return
        self.runtime._mark_step_failed(run, task, step, exc)

    def _self_heal(
        self, run: WorkflowRun, task, blueprint: ACGBlueprint, node_id: str, fault: InjectedFault
    ) -> bool:
        """对可恢复故障执行自愈：检查点 → 局部重规划 → 复位节点续跑。

        返回 True 表示已安排自愈续跑；False 表示无法自愈（交由失败逻辑）。
        若故障源仍会再次触发（未达自愈上限），仍复位重试以模拟有限重试自愈。
        """
        try:
            step = run.get_step(node_id)
        except KeyError:
            return False

        # 循环保护：单节点自愈重试上限，避免持续故障导致死循环。
        if step.retry_count >= 3:
            return False

        run.recovery_count += 1
        # 1) 故障事件入轨
        self.runtime.trace_store.append(
            run=run,
            event_type=TraceEventType.STEP_FAILED,
            step_id=node_id,
            agent_name=step.agent_name,
            observation=f"Injected fault: {fault.fault_type.value}",
            payload={"faultType": fault.fault_type.value, "recoverable": True},
        )
        # 2) 检查点（保存当前现场，供恢复定位）。直接复位节点状态属于恢复语义，
        #    与 native resume 一致地绕过状态机（无 RUNNING→PENDING 合法转换）。
        step.status = StepStatus.PENDING
        step.error = None
        step.retry_count += 1
        run.error = None
        checkpoint = self.runtime.checkpoint_store.create(run, node_id)
        # 3) 局部重规划轨迹：声明从检查点恢复、仅重跑该子图
        self.runtime.trace_store.append(
            run=run,
            event_type=TraceEventType.RUN_RECOVERED,
            step_id=node_id,
            agent_name=step.agent_name,
            observation=(
                f"Self-healing: recover from checkpoint {checkpoint.checkpoint_id}, "
                f"local replan re-runs step {node_id}"
            ),
            payload={
                "checkpointId": checkpoint.checkpoint_id,
                "strategy": "local_replan",
                "recoveryCount": run.recovery_count,
            },
        )
        return True

    @staticmethod
    def _safe_has_step(run: WorkflowRun, step_id: str) -> bool:
        try:
            run.get_step(step_id)
            return True
        except KeyError:
            return False

    def provenance_graph(self) -> dict:
        """导出数据血统图（供 API / 前端血缘面板）。"""
        return self.ledger.to_graph()


__all__ = ["ACGExecutor"]
