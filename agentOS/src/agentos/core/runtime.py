"""AgentOS Core 的正式运行时文件，延续原 core.workflow_runtime 的实现并承载任务、工作流、审核和恢复入口。"""


from __future__ import annotations

import os
from typing import Mapping, Optional

from agentos.agents import AgentRegistry
from agentos.core.acg import (
    ACGBlueprint,
    AgentNode,
    EdgeType,
    promote_workflow_to_acg,
)
from agentos.core.execution import ACGWorkflowAdapter, ExecutionAdapterFactory
from agentos.core.governance.checkpoint import CheckpointStore
from agentos.core.governance.evaluation import WorkflowEvaluator
from agentos.core.workflow.orchestrator import Orchestrator
from agentos.core.workflow.registry import WorkflowRegistry
from agentos.core.governance.review import ReviewManager
from agentos.core.workflow.state_machine import StateMachine
from agentos.core.workflow.task_manager import TaskManager
from agentos.core.governance.trace import TraceStore
from agentos.core.models.types import (
    AgentTask,
    Checkpoint,
    EvaluationRun,
    ReviewDecision,
    ReviewDecisionType,
    ReviewRecord,
    StepStatus,
    TraceEventType,
    WorkflowDefinition,
    WorkflowRun,
    WorkflowStatus,
    WorkflowStep,
    utc_now,
)
from agentos.packs.registry import register_installed_packs
from agentos.stores.memory_workflow_store import MemoryWorkflowStore
from agentos.stores.sqlite_workflow_store import SQLiteWorkflowStore
from agentos.stores.workflow_store import WorkflowStore


class WorkflowRuntime:
    """AgentOS Core 的工作流运行时，串联任务、Trace、审核与恢复流程。"""

    def __init__(
        self,
        *,
        agent_registry: Optional[AgentRegistry] = None,
        workflow_registry: Optional[WorkflowRegistry] = None,
        workflow_store: Optional[WorkflowStore] = None,
        trace_store: Optional[TraceStore] = None,
        checkpoint_store: Optional[CheckpointStore] = None,
        review_manager: Optional[ReviewManager] = None,
        evaluator: Optional[WorkflowEvaluator] = None,
        task_manager: Optional[TaskManager] = None,
        execution_adapter_factories: Optional[Mapping[str, ExecutionAdapterFactory]] = None,
    ):
        self.agent_registry = agent_registry or AgentRegistry()
        self.workflow_registry = workflow_registry or WorkflowRegistry()
        self.workflow_store = workflow_store or MemoryWorkflowStore()
        self.trace_store = trace_store or TraceStore()
        self.checkpoint_store = checkpoint_store or CheckpointStore()
        self.review_manager = review_manager or ReviewManager(self.trace_store)
        self.evaluator = evaluator or WorkflowEvaluator()
        self.state_machine = StateMachine()
        self.orchestrator = Orchestrator(self.agent_registry)
        self.task_manager = task_manager or TaskManager(
            workflow_store=self.workflow_store,
            workflow_registry=self.workflow_registry,
            state_machine=self.state_machine,
            trace_store=self.trace_store,
        )
        self._runtime_adapters: dict[str, object] = {}
        self.execution_adapter_factories: dict[str, ExecutionAdapterFactory] = {
            self._normalize_runtime_engine(engine): factory
            for engine, factory in (execution_adapter_factories or {}).items()
        }
        # 认知规划引擎（懒构造）。app 层可通过 set_intent_llm 注入真实 LLM，
        # 让意图解析走 DeepSeek；未注入时规划器用启发式回退。
        self._planning_engine = None
        self._intent_llm = None

    def set_intent_llm(self, intent_llm) -> None:
        """注入意图解析 LLM（app 层在装配时调用）。重置已构造的规划引擎。"""
        self._intent_llm = intent_llm
        self._planning_engine = None

    @property
    def planning_engine(self):
        if self._planning_engine is None:
            from agentos.core.planning import PlanningEngine

            self._planning_engine = PlanningEngine(
                workflow_registry=self.workflow_registry,
                agent_registry=self.agent_registry,
                intent_llm=self._intent_llm,
            )
        return self._planning_engine

    def register_execution_adapter(self, runtime_engine: str, factory: ExecutionAdapterFactory) -> None:
        engine = self._normalize_runtime_engine(runtime_engine)
        if engine == "acg":
            raise ValueError(f"{engine} runtime engine is built into AgentOS Core")
        self.execution_adapter_factories[engine] = factory

    def create_task(
        self,
        title: str,
        domain: str = "general",
        intent: str = "general",
        input: Optional[dict] = None,
        security_level: str = "internal",
        priority: str = "normal",
        *,
        role_type: Optional[str] = None,
        task_type: Optional[str] = None,
        workflow_id: Optional[str] = None,
    ) -> AgentTask:
        return self.task_manager.create_task(
            title=title,
            domain=domain,
            intent=intent,
            input=input,
            security_level=security_level,
            priority=priority,
            role_type=role_type,
            task_type=task_type,
            workflow_id=workflow_id,
        )

    async def start(
        self,
        task_id: str,
        workflow_id: Optional[str] = None,
        review_mode: str = "auto",
    ) -> WorkflowRun:
        task = self.task_manager.get_task(task_id)
        workflow = self._resolve_workflow(task, workflow_id)
        task = self.task_manager.mark_running(task)

        run = WorkflowRun(
            taskId=task.task_id,
            workflowId=workflow.workflow_id,
            domain=workflow.domain,
            runtimeEngine=workflow.effective_runtime_engine,
            implementationId=workflow.effective_implementation_id,
            currentStepId=workflow.first_step_id(),
            reviewMode=review_mode,
            input=dict(task.input),
            steps=[WorkflowStep.from_definition(step) for step in workflow.steps],
        )

        adapter = self._workflow_adapter(workflow)
        self._transition_run(run, WorkflowStatus.RUNNING)
        return await adapter.start(task=task, run=run, workflow=workflow)

    async def _start_acg(
        self,
        *,
        task: AgentTask,
        run: WorkflowRun,
        workflow: WorkflowDefinition,
        executor,
    ) -> WorkflowRun:
        """ACG 执行路径入口：构建蓝图并交给就绪集调度执行器。"""
        self.trace_store.append(
            run=run,
            event_type=TraceEventType.TASK_CREATED,
            observation=f"Task created: {task.title}",
            payload=task.model_dump(by_alias=True, mode="json"),
        )
        blueprint = self._build_acg_blueprint(task, run, workflow)
        self._validate_blueprint_agents(blueprint, domain=workflow.domain or task.domain)
        run.execution_state["workflowVersion"] = workflow.version
        run.execution_state["graphId"] = blueprint.graph_id
        run.execution_state["graphVersion"] = blueprint.version
        self._sync_run_steps_to_acg(run, blueprint)
        return await executor.run(task=task, run=run, workflow=workflow, blueprint=blueprint)

    def _validate_blueprint_agents(self, blueprint: ACGBlueprint, *, domain: str) -> None:
        missing: list[str] = []
        for step in blueprint.step_nodes():
            try:
                agent = self.agent_registry.resolve(
                    domain=domain,
                    agent_name=step.agent_name,
                    capability=step.capability,
                )
            except KeyError:
                missing.append(step.agent_name or step.node_id)
                continue

            execution_edges = blueprint.incoming(step.node_id, EdgeType.EXECUTION)
            if execution_edges:
                step.assigned_agent_id = execution_edges[0].source_id
            allowed_skills = list(dict.fromkeys(agent.profile.allowed_skills))
            if allowed_skills:
                step.metadata["allowedSkills"] = allowed_skills
            if step.assigned_agent_id:
                agent_node = blueprint.get_node(step.assigned_agent_id)
                if isinstance(agent_node, AgentNode) and allowed_skills:
                    existing = agent_node.metadata.get("allowedSkills")
                    existing_skills = existing if isinstance(existing, list) else []
                    agent_node.metadata["allowedSkills"] = list(
                        dict.fromkeys([*existing_skills, *allowed_skills])
                    )
        if missing:
            raise ValueError("ACG references unregistered Agents: " + ", ".join(sorted(set(missing))))
        blueprint.touch()

    def _build_acg_blueprint(
        self,
        task: AgentTask,
        run: WorkflowRun,
        workflow: WorkflowDefinition,
    ) -> ACGBlueprint:
        """获取 ACG 蓝图，三级优先级：

        1. 现成蓝图：run.input['acgBlueprint'] 或 run.acg_blueprint（外部/前序产物）。
        2. 认知规划引擎：task.input['usePlanner'] 为真，或工作流未定义 steps，
           则调 PlanningEngine 走“静态优选、动态补位”生成 ACG，并把规划决策入 Trace。
        3. 线性升格：默认把静态工作流定义无损升格（行为等价线性执行）。
        """
        provided = run.input.get("acgBlueprint") or (run.acg_blueprint if run.acg_blueprint else None)
        if isinstance(provided, dict) and provided.get("nodes"):
            blueprint = ACGBlueprint.model_validate(provided)
            if not blueprint.task_id:
                blueprint.task_id = task.task_id
            return blueprint

        planning_mode = str(task.input.get("planningMode") or "").strip().lower()
        force_dynamic = bool(task.input.get("forceDynamicPlanning")) or planning_mode == "dynamic"
        use_planner = force_dynamic or bool(task.input.get("usePlanner")) or not workflow.steps
        if use_planner:
            intent_text = str(
                task.input.get("userIntent")
                or task.input.get("intent")
                or task.title
                or workflow.description
            )
            plan = self.planning_engine.plan(
                task_id=task.task_id,
                intent=intent_text,
                domain=workflow.domain or task.domain,
                task_type=task.intent or workflow.intent,
                force_dynamic=force_dynamic,
            )
            self.trace_store.append(
                run=run,
                event_type=TraceEventType.TASK_STATUS_CHANGED,
                observation=f"Planner produced ACG via {plan.strategy}",
                payload=plan.to_decision(),
            )
            return plan.blueprint

        return promote_workflow_to_acg(workflow, task_id=task.task_id)

    def _sync_run_steps_to_acg(self, run: WorkflowRun, blueprint: ACGBlueprint) -> None:
        """让 WorkflowRun 的步骤列表与最终 ACG 蓝图保持一致。"""
        existing = {step.step_id: step for step in run.steps}
        synced: list[WorkflowStep] = []
        for node in blueprint.step_nodes():
            step = existing.get(node.node_id)
            if step is None:
                step = WorkflowStep(
                    stepId=node.node_id,
                    name=node.name or node.node_id,
                    agentName=node.agent_name or node.node_id,
                    capability=node.capability,
                    input=dict(node.input_spec),
                    outputSpec=dict(node.output_spec),
                    reviewRequired=node.review_required,
                    maxRetries=node.retry_limit,
                    timeout=node.timeout,
                    priority=node.priority,
                )
            else:
                step.name = node.name or step.name
                step.agent_name = node.agent_name or step.agent_name
                step.capability = node.capability
                step.input = dict(node.input_spec)
                step.output_spec = dict(node.output_spec)
                step.requires_review = node.review_required
                step.max_retries = node.retry_limit
                step.timeout = node.timeout
                step.priority = node.priority
            synced.append(step)

        run.steps = synced
        step_ids = {step.step_id for step in synced}
        if run.current_step_id not in step_ids:
            run.current_step_id = synced[0].step_id if synced else None

    async def _apply_acg_review(self, decision: ReviewDecision, *, executor) -> WorkflowRun:
        run = self.workflow_store.get_run(decision.run_id)
        task = self.task_manager.get_task(run.task_id)
        workflow = self.workflow_registry.get(run.workflow_id)
        step = run.get_step(decision.step_id)

        self.review_manager.record(run, decision)
        blueprint = ACGBlueprint.model_validate(run.acg_blueprint) if run.acg_blueprint else promote_workflow_to_acg(workflow, task_id=task.task_id)

        if decision.decision == ReviewDecisionType.APPROVED:
            self._transition_step(step, StepStatus.COMPLETED)
            completed = set(run.completed_step_ids)
            completed.add(step.step_id)
            run.completed_step_ids = sorted(completed)
            self._transition_run(run, WorkflowStatus.RUNNING)
            self.task_manager.mark_running(task)
            self.workflow_store.save_run(run)
            return await executor.resume(task=task, run=run, workflow=workflow, blueprint=blueprint)

        if decision.decision == ReviewDecisionType.RERUN:
            step.retry_count += 1
            self._transition_step(step, StepStatus.RETRYING)
            self._transition_run(run, WorkflowStatus.RETRYING)
            self.task_manager.mark_retrying(task)
            self.workflow_store.save_run(run)
            return await executor.resume(task=task, run=run, workflow=workflow, blueprint=blueprint)

        if decision.decision == ReviewDecisionType.CANCELLED:
            return self.cancel(run.run_id)

        if decision.decision == ReviewDecisionType.NEED_MORE_INFO:
            step.status = StepStatus.WAITING_REVIEW
            self._transition_run_if_needed(run, WorkflowStatus.WAITING_REVIEW)
            run.error = decision.comment or "Reviewer requested more information."
            self.task_manager.mark_waiting_review(task)
            self.workflow_store.save_run(run)
            return run

        # REJECTED
        self._transition_step(step, StepStatus.FAILED)
        self._transition_run(run, WorkflowStatus.FAILED)
        run.error = decision.comment or "Review rejected workflow step."
        self.task_manager.mark_failed(task)
        self.trace_store.append(
            run=run,
            event_type=TraceEventType.RUN_FAILED,
            step_id=step.step_id,
            observation=run.error,
        )
        self.workflow_store.save_run(run)
        return run

    def _transition_run_if_needed(self, run: WorkflowRun, status: WorkflowStatus) -> None:
        if run.status != status:
            self._transition_run(run, status)

    def get_status(self, run_id: str) -> WorkflowRun:
        return self.workflow_store.get_run(run_id)

    def resolve_workflow_id(self, workflow_id: str | None) -> str | None:
        if not workflow_id:
            return workflow_id
        return self.workflow_registry.get(workflow_id).workflow_id

    def list_checkpoints(self, run_id: str) -> list[Checkpoint]:
        return self.checkpoint_store.list(self.workflow_store.get_run(run_id))

    def list_reviews(self, run_id: str) -> list[ReviewRecord]:
        return self.review_manager.list(self.workflow_store.get_run(run_id))

    def evaluate_runs(
        self,
        *,
        status: WorkflowStatus | str | None = None,
        domain: str | None = None,
        workflow_id: str | None = None,
        source: str | None = None,
    ) -> EvaluationRun:
        workflow_id = self.resolve_workflow_id(workflow_id)
        page = self.workflow_store.list_runs(
            status=status,
            domain=domain,
            workflow_id=workflow_id,
            source=source,
            page=1,
            page_size=10_000,
        )
        return self.evaluator.evaluate(
            page.items,
            domain=domain,
            workflow_id=workflow_id,
            source=source,
        )

    async def apply_review(self, decision: ReviewDecision) -> WorkflowRun:
        run = self.workflow_store.get_run(decision.run_id)
        workflow = self.workflow_registry.get(run.workflow_id)
        adapter = self._workflow_adapter(workflow)
        return await adapter.apply_review(decision)

    async def resume_from_checkpoint(self, *, run_id: str, checkpoint_id: str) -> WorkflowRun:
        run = self.workflow_store.get_run(run_id)
        task = self.task_manager.get_task(run.task_id)
        workflow = self.workflow_registry.get(run.workflow_id)
        checkpoint = self.checkpoint_store.find(run, checkpoint_id)
        if run.runtime_engine != "acg" or workflow.effective_runtime_engine != "acg":
            raise ValueError("Only acg workflow runs can be resumed from checkpoints")

        snapshot = checkpoint.state_snapshot or {}
        snapshot_workflow_version = snapshot.get("workflowVersion")
        if snapshot_workflow_version and snapshot_workflow_version != workflow.version:
            raise ValueError(
                f"Checkpoint workflow version mismatch: {snapshot_workflow_version} != {workflow.version}"
            )
        snapshot_steps = snapshot.get("steps")
        if isinstance(snapshot_steps, list):
            run.steps = [WorkflowStep.model_validate(step) for step in snapshot_steps]
        run.acg_blueprint = snapshot.get("acgBlueprint") or run.acg_blueprint
        completed = snapshot.get("completedStepIds")
        if isinstance(completed, list):
            run.completed_step_ids = sorted({str(step_id) for step_id in completed})
        else:
            run.completed_step_ids = sorted(
                step.step_id for step in run.steps if step.status == StepStatus.COMPLETED
            )
        run.current_step_id = snapshot.get("currentStepId") or checkpoint.step_id
        if "provenance" in snapshot:
            run.provenance = snapshot["provenance"]
        if isinstance(snapshot.get("executionState"), dict):
            run.execution_state = dict(snapshot["executionState"])
        run.active_step_ids = []
        if "output" in snapshot:
            run.output = dict(snapshot["output"] or {})
        blueprint = (
            ACGBlueprint.model_validate(run.acg_blueprint)
            if run.acg_blueprint
            else promote_workflow_to_acg(workflow, task_id=task.task_id)
        )
        run.acg_blueprint = blueprint.model_dump(by_alias=True, mode="json")
        snapshot_graph_id = snapshot.get("graphId")
        snapshot_graph_version = snapshot.get("graphVersion")
        if snapshot_graph_id and snapshot_graph_id != blueprint.graph_id:
            raise ValueError(f"Checkpoint graph mismatch: {snapshot_graph_id} != {blueprint.graph_id}")
        if snapshot_graph_version is not None and int(snapshot_graph_version) != blueprint.version:
            raise ValueError(
                f"Checkpoint graph version mismatch: {snapshot_graph_version} != {blueprint.version}"
            )

        for step in run.steps:
            if step.status == StepStatus.RUNNING:
                step.status = StepStatus.RETRYING

        self._transition_run(run, WorkflowStatus.RETRYING)
        run.error = None
        run.recovery_count += 1
        self.task_manager.mark_retrying(task)
        self.trace_store.append(
            run=run,
            event_type=TraceEventType.RUN_RECOVERED,
            step_id=checkpoint.step_id,
            observation=f"Recovered from checkpoint: {checkpoint.checkpoint_id}",
            payload=checkpoint.model_dump(by_alias=True, mode="json"),
        )
        self.workflow_store.save_run(run)
        adapter = self._workflow_adapter(workflow)
        assert isinstance(adapter, ACGWorkflowAdapter)
        return await adapter.new_executor().resume(
            task=task,
            run=run,
            workflow=workflow,
            blueprint=blueprint,
        )

    def cancel(self, run_id: str) -> WorkflowRun:
        run = self.workflow_store.get_run(run_id)
        self._transition_run(run, WorkflowStatus.CANCELLED)
        for step in run.steps:
            if step.status in {
                StepStatus.PENDING,
                StepStatus.RUNNING,
                StepStatus.RETRYING,
                StepStatus.WAITING_REVIEW,
            }:
                self._transition_step(step, StepStatus.CANCELLED)
        self.task_manager.mark_cancelled(run.task_id)
        self.trace_store.append(
            run=run,
            event_type=TraceEventType.RUN_CANCELLED,
            observation="Workflow cancelled.",
        )
        self.workflow_store.save_run(run)
        return run

    def _resolve_workflow(self, task: AgentTask, workflow_id: Optional[str]) -> WorkflowDefinition:
        return self.task_manager.bind_workflow(task, workflow_id=workflow_id)

    def _workflow_adapter(self, workflow: WorkflowDefinition):
        runtime_engine = workflow.effective_runtime_engine
        implementation_id = workflow.effective_implementation_id
        adapter_key = f"{runtime_engine}:{implementation_id}"
        adapter = self._runtime_adapters.get(adapter_key)
        if adapter is None:
            if runtime_engine == "acg":
                adapter = ACGWorkflowAdapter(self)
            else:
                factory = self.execution_adapter_factories.get(runtime_engine)
                if factory is None:
                    raise ValueError(f"Unsupported workflow runtime engine: {runtime_engine}")
                adapter = factory(
                    runtime=self,
                    workflow=workflow,
                    implementation_id=implementation_id,
                )
            self._runtime_adapters[adapter_key] = adapter
        return adapter

    @staticmethod
    def _normalize_runtime_engine(runtime_engine: str) -> str:
        return (runtime_engine or "").strip().lower()

    def _mark_step_failed(
        self,
        run: WorkflowRun,
        task: AgentTask,
        step: WorkflowStep,
        exc: Exception,
    ) -> None:
        step.error = str(exc)
        if step.retry_count < step.max_retries:
            step.retry_count += 1
            self._transition_step(step, StepStatus.RETRYING)
            self._transition_run(run, WorkflowStatus.RETRYING)
            self.task_manager.mark_retrying(task)
        else:
            self._transition_step(step, StepStatus.FAILED)
            self._transition_run(run, WorkflowStatus.FAILED)
            self.task_manager.mark_failed(task)
        run.current_step_id = step.step_id
        run.error = str(exc)
        run.updated_at = utc_now()
        self.trace_store.append(
            run=run,
            event_type=TraceEventType.STEP_FAILED,
            step_id=step.step_id,
            agent_name=step.agent_name,
            observation=str(exc),
        )
        self.trace_store.append(
            run=run,
            event_type=TraceEventType.RUN_FAILED,
            step_id=step.step_id,
            observation=str(exc),
        )
        self.workflow_store.save_run(run)

    def _transition_run(self, run: WorkflowRun, status: WorkflowStatus) -> None:
        run.status = self.state_machine.transition(run.status, status)
        run.updated_at = utc_now()

    def _transition_step(self, step: WorkflowStep, status: StepStatus) -> None:
        step.status = self.state_machine.transition(step.status, status)
        if status == StepStatus.RUNNING:
            step.started_at = step.started_at or utc_now()
        if status == StepStatus.COMPLETED:
            step.completed_at = step.completed_at or utc_now()

    def _complete_run(self, task: AgentTask, run: WorkflowRun) -> None:
        self._transition_run(run, WorkflowStatus.COMPLETED)
        run.current_step_id = None
        run.output = self.orchestrator.compose_final_output(run)
        self.task_manager.mark_completed(task)
        self.trace_store.append(
            run=run,
            event_type=TraceEventType.RUN_COMPLETED,
            observation="Workflow completed.",
            payload=run.output,
        )

    def _create_checkpoint(self, run: WorkflowRun, step: WorkflowStep) -> Checkpoint:
        checkpoint = self.checkpoint_store.create(run, step.step_id)
        self.trace_store.append(
            run=run,
            event_type=TraceEventType.CHECKPOINT_CREATED,
            step_id=step.step_id,
            observation=f"Checkpoint created: {checkpoint.checkpoint_id}",
            payload=checkpoint.model_dump(by_alias=True, mode="json"),
        )
        return checkpoint


def build_default_runtime() -> WorkflowRuntime:
    agent_registry = AgentRegistry()
    workflow_registry = WorkflowRegistry()

    db_path = os.getenv("AGENTOS_WORKFLOW_DB_PATH", "").strip()
    workflow_store: WorkflowStore
    if db_path:
        workflow_store = SQLiteWorkflowStore(db_path)
    else:
        workflow_store = MemoryWorkflowStore()

    runtime = WorkflowRuntime(
        agent_registry=agent_registry,
        workflow_registry=workflow_registry,
        workflow_store=workflow_store,
    )
    register_installed_packs(
        agent_registry=runtime.agent_registry,
        workflow_registry=runtime.workflow_registry,
    )
    return runtime


__all__ = ["WorkflowRuntime", "build_default_runtime"]
