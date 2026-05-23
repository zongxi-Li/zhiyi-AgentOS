"""AgentOS Core 的正式运行时文件，延续原 core.workflow_runtime 的实现并承载任务、工作流、审核和恢复入口。"""


from __future__ import annotations

import os
from typing import Optional

from agentos.agents import AgentRegistry
from agentos.core.execution import LangGraphAdapter, NativeWorkflowAdapter
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
from agentos.memory.workflow_memory import WorkflowMemory
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

    async def _start_native(self, *, task: AgentTask, run: WorkflowRun, workflow: WorkflowDefinition) -> WorkflowRun:
        self._transition_run(run, WorkflowStatus.RUNNING)
        self.trace_store.append(
            run=run,
            event_type=TraceEventType.TASK_CREATED,
            observation=f"Task created: {task.title}",
            payload=task.model_dump(by_alias=True, mode="json"),
        )
        self.trace_store.append(
            run=run,
            event_type=TraceEventType.RUN_STARTED,
            observation=f"Workflow started: {workflow.workflow_id}",
            payload={"workflowId": workflow.workflow_id, "reviewMode": run.review_mode},
        )
        self.workflow_store.save_run(run)
        return await self._run_until_blocked(task, run, workflow)

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

    async def _apply_native_review(self, decision: ReviewDecision) -> WorkflowRun:
        run = self.workflow_store.get_run(decision.run_id)
        task = self.task_manager.get_task(run.task_id)
        workflow = self.workflow_registry.get(run.workflow_id)
        step = run.get_step(decision.step_id)

        self.review_manager.record(run, decision)
        if decision.decision == ReviewDecisionType.APPROVED:
            self._transition_step(step, StepStatus.COMPLETED)
            run.current_step_id = workflow.next_step_id(step.step_id)
            if run.current_step_id is None:
                self._complete_run(task, run)
                self.workflow_store.save_run(run)
                return run

            self._transition_run(run, WorkflowStatus.RUNNING)
            self.task_manager.mark_running(task)
            self.workflow_store.save_run(run)
            return await self._run_until_blocked(task, run, workflow)

        if decision.decision == ReviewDecisionType.RERUN:
            step.retry_count += 1
            self._transition_step(step, StepStatus.RETRYING)
            self._transition_run(run, WorkflowStatus.RETRYING)
            run.current_step_id = step.step_id
            self.task_manager.mark_retrying(task)
            self.workflow_store.save_run(run)
            return await self._run_until_blocked(task, run, workflow)

        if decision.decision == ReviewDecisionType.CANCELLED:
            return self.cancel(run.run_id)

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

    async def resume_from_checkpoint(self, *, run_id: str, checkpoint_id: str) -> WorkflowRun:
        run = self.workflow_store.get_run(run_id)
        task = self.task_manager.get_task(run.task_id)
        workflow = self.workflow_registry.get(run.workflow_id)
        checkpoint = self.checkpoint_store.find(run, checkpoint_id)

        snapshot = checkpoint.state_snapshot or {}
        snapshot_steps = snapshot.get("steps")
        if isinstance(snapshot_steps, list):
            run.steps = [WorkflowStep.model_validate(step) for step in snapshot_steps]

        self._transition_run(run, WorkflowStatus.RETRYING)
        run.current_step_id = self._next_pending_step_id(run)
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
        return await self._run_until_blocked(task, run, workflow)

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
            if runtime_engine == "native":
                adapter = NativeWorkflowAdapter(self)
            elif runtime_engine == "langgraph":
                adapter = LangGraphAdapter(runtime=self, implementation_id=implementation_id)
            else:
                raise ValueError(f"Unsupported workflow runtime engine: {runtime_engine}")
            self._runtime_adapters[adapter_key] = adapter
        return adapter

    async def _run_until_blocked(
        self,
        task: AgentTask,
        run: WorkflowRun,
        workflow: WorkflowDefinition,
    ) -> WorkflowRun:
        self._transition_run(run, WorkflowStatus.RUNNING)
        self.task_manager.mark_running(task)

        while True:
            step = self.orchestrator.select_next_step(run)
            if step is None:
                self._complete_run(task, run)
                self.workflow_store.save_run(run)
                return run

            run.current_step_id = step.step_id
            self._transition_step(step, StepStatus.RUNNING)
            run.updated_at = utc_now()
            self.trace_store.append(
                run=run,
                event_type=TraceEventType.STEP_STARTED,
                step_id=step.step_id,
                agent_name=step.agent_name,
                observation=f"Step started: {step.name}",
            )
            self.workflow_store.save_run(run)

            memory = WorkflowMemory.from_run(run)
            try:
                result, duration_ms = await self.orchestrator.dispatch_agent(
                    task=task,
                    run=run,
                    workflow=workflow,
                    step=step,
                    memory=memory,
                )
            except Exception as exc:
                self._mark_step_failed(run, task, step, exc)
                return run

            step.output = dict(result.output)
            memory.record(step.step_id, step.output)
            self.trace_store.append(
                run=run,
                event_type=TraceEventType.AGENT_CALLED,
                step_id=step.step_id,
                agent_name=step.agent_name,
                observation=result.summary or f"Agent completed: {step.agent_name}",
                payload=step.output,
                duration_ms=duration_ms,
            )

            if step.requires_review and run.review_mode != "auto":
                self._transition_step(step, StepStatus.WAITING_REVIEW)
                self._transition_run(run, WorkflowStatus.WAITING_REVIEW)
                run.current_step_id = step.step_id
                self.task_manager.mark_waiting_review(task)
                self._create_checkpoint(run, step)
                self.trace_store.append(
                    run=run,
                    event_type=TraceEventType.REVIEW_REQUIRED,
                    step_id=step.step_id,
                    agent_name=step.agent_name,
                    observation=f"Review required for step: {step.step_id}",
                    payload=step.output,
                )
                self.workflow_store.save_run(run)
                return run

            self._transition_step(step, StepStatus.COMPLETED)
            self._create_checkpoint(run, step)
            run.current_step_id = workflow.next_step_id(step.step_id)
            run.updated_at = utc_now()
            self.workflow_store.save_run(run)

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

    def _next_pending_step_id(self, run: WorkflowRun) -> Optional[str]:
        for step in run.steps:
            if step.status in {StepStatus.PENDING, StepStatus.RETRYING, StepStatus.FAILED}:
                if step.status == StepStatus.FAILED:
                    self._transition_step(step, StepStatus.RETRYING)
                return step.step_id
        return None

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
