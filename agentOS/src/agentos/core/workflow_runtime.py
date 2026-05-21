from __future__ import annotations

import os
from typing import Optional

from agentos.agents import AgentRegistry
from agentos.core.checkpoint import CheckpointStore
from agentos.core.evaluation import WorkflowEvaluator
from agentos.core.orchestrator import Orchestrator
from agentos.core.registry import WorkflowRegistry
from agentos.core.review import ReviewManager
from agentos.core.state_machine import StateMachine
from agentos.core.trace import TraceStore
from agentos.core.types import (
    AgentTask,
    Checkpoint,
    ReviewDecision,
    ReviewDecisionType,
    ReviewRecord,
    StepStatus,
    TraceEventType,
    WorkflowDefinition,
    WorkflowMetric,
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
    """AgentOS Core runtime for task, workflow, trace, review, and recovery flows."""

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

    def create_task(
        self,
        title: str,
        domain: str = "general",
        intent: str = "general",
        input: Optional[dict] = None,
        security_level: str = "internal",
        priority: str = "normal",
    ) -> AgentTask:
        workflow = self.workflow_registry.recommend(domain=domain, intent=intent)
        task = AgentTask(
            title=title,
            domain=domain,
            intent=intent,
            input=input or {},
            securityLevel=security_level,
            priority=priority,
            recommendedWorkflow=workflow.workflow_id if workflow else None,
        )
        self.workflow_store.save_task(task)
        return task

    async def start(
        self,
        task_id: str,
        workflow_id: Optional[str] = None,
        review_mode: str = "auto",
    ) -> WorkflowRun:
        task = self.workflow_store.get_task(task_id)
        workflow = self._resolve_workflow(task, workflow_id)
        task.recommended_workflow = workflow.workflow_id
        task.status = WorkflowStatus.RUNNING
        task.updated_at = utc_now()
        self.workflow_store.save_task(task)

        run = WorkflowRun(
            taskId=task.task_id,
            workflowId=workflow.workflow_id,
            domain=workflow.domain,
            status=WorkflowStatus.RUNNING,
            currentStepId=workflow.first_step_id(),
            reviewMode=review_mode,
            input=dict(task.input),
            steps=[WorkflowStep.from_definition(step) for step in workflow.steps],
        )
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
            payload={"workflowId": workflow.workflow_id, "reviewMode": review_mode},
        )
        self.workflow_store.save_run(run)
        return await self._run_until_blocked(task, run, workflow)

    def get_status(self, run_id: str) -> WorkflowRun:
        return self.workflow_store.get_run(run_id)

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
    ):
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
        task = self.workflow_store.get_task(run.task_id)
        workflow = self.workflow_registry.get(run.workflow_id)
        step = run.get_step(decision.step_id)

        self.review_manager.record(run, decision)
        if decision.decision == ReviewDecisionType.APPROVED:
            step.status = StepStatus.COMPLETED
            step.completed_at = step.completed_at or utc_now()
            run.status = WorkflowStatus.RUNNING
            run.current_step_id = workflow.next_step_id(step.step_id)
            run.updated_at = utc_now()
            self.workflow_store.save_run(run)
            return await self._run_until_blocked(task, run, workflow)

        if decision.decision == ReviewDecisionType.RERUN:
            step.status = StepStatus.RETRYING
            step.retry_count += 1
            run.status = WorkflowStatus.RETRYING
            run.current_step_id = step.step_id
            run.updated_at = utc_now()
            self.workflow_store.save_run(run)
            return await self._run_until_blocked(task, run, workflow)

        if decision.decision == ReviewDecisionType.CANCELLED:
            return self.cancel(run.run_id)

        step.status = StepStatus.FAILED
        run.status = WorkflowStatus.FAILED
        run.error = decision.comment or "Review rejected workflow step."
        run.updated_at = utc_now()
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
        task = self.workflow_store.get_task(run.task_id)
        workflow = self.workflow_registry.get(run.workflow_id)
        checkpoint = self.checkpoint_store.find(run, checkpoint_id)

        snapshot = checkpoint.state_snapshot or {}
        snapshot_steps = snapshot.get("steps")
        if isinstance(snapshot_steps, list):
            run.steps = [WorkflowStep.model_validate(step) for step in snapshot_steps]

        run.status = WorkflowStatus.RETRYING
        run.current_step_id = self._next_pending_step_id(run)
        run.error = None
        run.recovery_count += 1
        run.updated_at = utc_now()
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
        run.status = WorkflowStatus.CANCELLED
        for step in run.steps:
            if step.status in {
                StepStatus.PENDING,
                StepStatus.RUNNING,
                StepStatus.RETRYING,
                StepStatus.WAITING_REVIEW,
            }:
                step.status = StepStatus.CANCELLED
        run.updated_at = utc_now()
        self.trace_store.append(
            run=run,
            event_type=TraceEventType.RUN_CANCELLED,
            observation="Workflow cancelled.",
        )
        self.workflow_store.save_run(run)
        return run

    def _resolve_workflow(self, task: AgentTask, workflow_id: Optional[str]) -> WorkflowDefinition:
        if workflow_id:
            return self.workflow_registry.get(workflow_id)
        if task.recommended_workflow:
            return self.workflow_registry.get(task.recommended_workflow)
        workflow = self.workflow_registry.recommend(domain=task.domain, intent=task.intent)
        if workflow is None:
            raise KeyError(f"workflow not found for domain={task.domain}, intent={task.intent}")
        return workflow

    async def _run_until_blocked(
        self,
        task: AgentTask,
        run: WorkflowRun,
        workflow: WorkflowDefinition,
    ) -> WorkflowRun:
        run.status = WorkflowStatus.RUNNING

        while True:
            step = self.orchestrator.select_next_step(run)
            if step is None:
                run.status = WorkflowStatus.COMPLETED
                run.current_step_id = None
                run.output = self.orchestrator.compose_final_output(run)
                run.updated_at = utc_now()
                task.status = WorkflowStatus.COMPLETED
                task.updated_at = utc_now()
                self.trace_store.append(
                    run=run,
                    event_type=TraceEventType.RUN_COMPLETED,
                    observation="Workflow completed.",
                    payload=run.output,
                )
                self.workflow_store.save_task(task)
                self.workflow_store.save_run(run)
                return run

            run.current_step_id = step.step_id
            step.status = StepStatus.RUNNING
            step.started_at = step.started_at or utc_now()
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
            step.status = StepStatus.COMPLETED
            step.completed_at = utc_now()
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
            checkpoint = self.checkpoint_store.create(run, step.step_id)
            self.trace_store.append(
                run=run,
                event_type=TraceEventType.CHECKPOINT_CREATED,
                step_id=step.step_id,
                observation=f"Checkpoint created: {checkpoint.checkpoint_id}",
                payload=checkpoint.model_dump(by_alias=True, mode="json"),
            )

            if step.requires_review and run.review_mode != "auto":
                step.status = StepStatus.WAITING_REVIEW
                run.status = WorkflowStatus.WAITING_REVIEW
                run.current_step_id = step.step_id
                run.updated_at = utc_now()
                task.status = WorkflowStatus.WAITING_REVIEW
                task.updated_at = utc_now()
                self.trace_store.append(
                    run=run,
                    event_type=TraceEventType.REVIEW_REQUIRED,
                    step_id=step.step_id,
                    agent_name=step.agent_name,
                    observation=f"Review required for step: {step.step_id}",
                    payload=step.output,
                )
                self.workflow_store.save_task(task)
                self.workflow_store.save_run(run)
                return run

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
            step.status = StepStatus.RETRYING
            run.status = WorkflowStatus.RETRYING
        else:
            step.status = StepStatus.FAILED
            run.status = WorkflowStatus.FAILED
            task.status = WorkflowStatus.FAILED
        run.current_step_id = step.step_id
        run.error = str(exc)
        run.updated_at = utc_now()
        task.updated_at = utc_now()
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
        self.workflow_store.save_task(task)
        self.workflow_store.save_run(run)

    def _next_pending_step_id(self, run: WorkflowRun) -> Optional[str]:
        for step in run.steps:
            if step.status in {StepStatus.PENDING, StepStatus.RETRYING, StepStatus.FAILED}:
                if step.status == StepStatus.FAILED:
                    step.status = StepStatus.RETRYING
                return step.step_id
        return None


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
