from __future__ import annotations

import os
from typing import Optional

from agentos.agents import AgentRegistry
from agentos.memory.workflow_memory import WorkflowMemory
from agentos.core.checkpoint import CheckpointStore
from agentos.core.evaluation import WorkflowEvaluator
from agentos.core.orchestrator import Orchestrator
from agentos.core.review import ReviewManager
from agentos.core.state_machine import StateMachine
from agentos.stores.memory_workflow_store import MemoryWorkflowStore
from agentos.stores.sqlite_workflow_store import SQLiteWorkflowStore
from agentos.stores.workflow_store import WorkflowStore
from agentos.packs.registry import register_installed_packs
from agentos.core.trace import TraceStore
from agentos.core.types import (
    AgentTask,
    ReviewDecision,
    ReviewDecisionType,
    Checkpoint,
    EvaluationRun,
    ReviewRecord,
    StepStatus,
    TraceEventType,
    WorkflowRun,
    WorkflowStatus,
    WorkflowStep,
)
from agentos.core.types import utc_now
from agentos.core.workflow_registry import WorkflowRegistry


class WorkflowRuntime:
    """AgentOS Core runtime for task and workflow lifecycles."""

    def __init__(
        self,
        agent_registry: AgentRegistry,
        workflow_registry: WorkflowRegistry,
        state_machine: Optional[StateMachine] = None,
        trace_store: Optional[TraceStore] = None,
        checkpoint_store: Optional[CheckpointStore] = None,
        workflow_store: Optional[WorkflowStore] = None,
    ):
        self.agent_registry = agent_registry
        self.workflow_registry = workflow_registry
        self.state_machine = state_machine or StateMachine()
        self.trace_store = trace_store or TraceStore()
        self.checkpoint_store = checkpoint_store or CheckpointStore()
        self.workflow_store = workflow_store or MemoryWorkflowStore()
        self.review_manager = ReviewManager(self.trace_store)
        self.evaluator = WorkflowEvaluator()
        self.orchestrator = Orchestrator(agent_registry=agent_registry)

    def create_task(
        self,
        title: str,
        domain: str,
        intent: str,
        input: Optional[dict] = None,
        security_level: str = "internal",
        priority: str = "normal",
    ) -> AgentTask:
        recommended = self.workflow_registry.recommend(domain=domain, intent=intent)
        task = AgentTask(
            title=title,
            domain=domain,
            intent=intent,
            input=input or {},
            securityLevel=security_level,
            priority=priority,
            recommendedWorkflow=recommended.workflow_id if recommended else None,
        )
        self.workflow_store.save_task(task)
        return task

    async def start(
        self,
        task_id: str,
        workflow_id: Optional[str] = None,
        review_mode: str = "auto",
    ) -> WorkflowRun:
        task = self._get_task(task_id)
        workflow = self._resolve_workflow(task=task, workflow_id=workflow_id)
        steps = [WorkflowStep.from_definition(step) for step in workflow.steps]
        run = WorkflowRun(
            taskId=task.task_id,
            workflowId=workflow.workflow_id,
            domain=workflow.domain,
            currentStepId=workflow.first_step_id(),
            reviewMode=review_mode,
            input=dict(task.input),
            steps=steps,
        )
        self.workflow_store.save_run(run)
        task.status = WorkflowStatus.RUNNING
        task.updated_at = utc_now()
        self.workflow_store.save_task(task)

        self.trace_store.append(
            run,
            TraceEventType.TASK_CREATED,
            observation=f"Task created: {task.title}",
            payload=task.model_dump(by_alias=True, mode="json"),
        )
        self.trace_store.append(
            run,
            TraceEventType.RUN_STARTED,
            observation=f"Workflow run started: {workflow.workflow_id}",
            payload={"workflowId": workflow.workflow_id, "reviewMode": review_mode},
        )
        return await self._run_until_blocked(task=task, run=run)

    def get_status(self, run_id: str) -> WorkflowRun:
        return self._get_run(run_id)

    def list_checkpoints(self, run_id: str) -> list[Checkpoint]:
        return self.checkpoint_store.list(self._get_run(run_id))

    def list_reviews(self, run_id: str) -> list[ReviewRecord]:
        return self.review_manager.list(self._get_run(run_id))

    def evaluate_runs(
        self,
        *,
        status: WorkflowStatus | str | None = None,
        domain: str | None = None,
        workflow_id: str | None = None,
        source: str | None = None,
    ) -> EvaluationRun:
        runs = self.workflow_store.list_runs(
            status=status,
            domain=domain,
            workflow_id=workflow_id,
            source=source,
            page=1,
            page_size=10000,
        )
        return self.evaluator.evaluate(
            runs.items,
            domain=domain,
            workflow_id=workflow_id,
            source=source,
        )

    async def apply_review(self, decision: ReviewDecision) -> WorkflowRun:
        run = self._get_run(decision.run_id)
        task = self._get_task(run.task_id)
        step = run.get_step(decision.step_id)
        self.review_manager.record(run, decision)

        if decision.decision == ReviewDecisionType.APPROVED:
            step.status = StepStatus.COMPLETED
            step.completed_at = utc_now()
            workflow = self.workflow_registry.get(run.workflow_id)
            run.current_step_id = workflow.next_step_id(step.step_id)
            self._checkpoint(run, step.step_id)
            run.status = WorkflowStatus.RUNNING if run.current_step_id else WorkflowStatus.COMPLETED
            self.workflow_store.save_run(run)
            return await self._run_until_blocked(task=task, run=run)

        if decision.decision == ReviewDecisionType.RERUN:
            step.status = StepStatus.RETRYING
            step.error = None
            step.retry_count += 1
            step.output = {}
            run.status = WorkflowStatus.RETRYING
            run.current_step_id = step.step_id
            self.workflow_store.save_run(run)
            return await self._run_until_blocked(task=task, run=run)

        if decision.decision == ReviewDecisionType.CANCELLED:
            return self.cancel(run.run_id, reason=decision.comment or "cancelled by reviewer")

        step.status = StepStatus.FAILED
        step.error = decision.comment or "rejected by reviewer"
        run.status = WorkflowStatus.FAILED
        run.error = step.error
        run.updated_at = utc_now()
        self.trace_store.append(
            run,
            TraceEventType.RUN_FAILED,
            step_id=step.step_id,
            observation=run.error,
        )
        self.workflow_store.save_run(run)
        return run

    async def resume_from_checkpoint(self, run_id: str, checkpoint_id: str) -> WorkflowRun:
        run = self._get_run(run_id)
        task = self._get_task(run.task_id)
        checkpoint = self.checkpoint_store.find(run, checkpoint_id)
        snapshot = checkpoint.state_snapshot

        run.steps = [WorkflowStep.model_validate(step) for step in snapshot.get("steps", [])]
        run.input = dict(snapshot.get("input", {}))
        run.output = dict(snapshot.get("output", {}))
        run.current_step_id = snapshot.get("currentStepId")
        run.status = WorkflowStatus.RETRYING
        run.error = None
        run.recovery_count += 1
        run.updated_at = utc_now()
        self.trace_store.append(
            run,
            TraceEventType.RUN_RECOVERED,
            step_id=checkpoint.step_id,
            observation=f"Recovered from checkpoint {checkpoint.checkpoint_id}",
            payload={"checkpointId": checkpoint.checkpoint_id},
        )
        self.workflow_store.save_run(run)
        return await self._run_until_blocked(task=task, run=run)

    def cancel(self, run_id: str, reason: str = "cancelled") -> WorkflowRun:
        run = self._get_run(run_id)
        run.status = WorkflowStatus.CANCELLED
        run.error = reason
        run.updated_at = utc_now()
        self.trace_store.append(run, TraceEventType.RUN_CANCELLED, observation=reason)
        self.workflow_store.save_run(run)
        return run

    async def _run_until_blocked(self, task: AgentTask, run: WorkflowRun) -> WorkflowRun:
        while run.status not in {
            WorkflowStatus.WAITING_REVIEW,
            WorkflowStatus.FAILED,
            WorkflowStatus.COMPLETED,
            WorkflowStatus.CANCELLED,
        }:
            step = self.orchestrator.select_next_step(run)
            if step is None:
                self._complete_run(task=task, run=run)
                break
            await self._run_step(task=task, run=run, step=step)
        self.workflow_store.save_run(run)
        return run

    async def _run_step(self, task: AgentTask, run: WorkflowRun, step: WorkflowStep) -> None:
        workflow = self.workflow_registry.get(run.workflow_id)

        try:
            run.status = self.state_machine.transition(run.status, WorkflowStatus.RUNNING)
        except Exception:
            run.status = WorkflowStatus.RUNNING

        step.status = self.state_machine.transition(step.status, StepStatus.RUNNING)
        step.started_at = utc_now()
        step.error = None
        run.current_step_id = step.step_id
        run.updated_at = utc_now()
        self.workflow_store.save_run(run)
        self.trace_store.append(
            run,
            TraceEventType.STEP_STARTED,
            step_id=step.step_id,
            agent_name=step.agent_name,
            observation=f"Step started: {step.name}",
        )

        try:
            memory = WorkflowMemory.from_run(run)
            result, duration_ms = await self.orchestrator.dispatch_agent(
                task=task,
                run=run,
                workflow=workflow,
                step=step,
                memory=memory,
            )
            step.output = dict(result.output)
            step.completed_at = utc_now()
            self.trace_store.append(
                run,
                TraceEventType.AGENT_CALLED,
                step_id=step.step_id,
                agent_name=step.agent_name,
                observation=result.summary or f"Agent {step.agent_name} completed.",
                payload=step.output,
                duration_ms=duration_ms,
            )

            if step.requires_review and run.review_mode == "human_in_loop":
                step.status = StepStatus.WAITING_REVIEW
                run.status = WorkflowStatus.WAITING_REVIEW
                run.current_step_id = step.step_id
                self._checkpoint(run, step.step_id)
                self.trace_store.append(
                    run,
                    TraceEventType.REVIEW_REQUIRED,
                    step_id=step.step_id,
                    agent_name=step.agent_name,
                    observation=f"Step waiting for review: {step.name}",
                )
                return

            self._complete_step(run=run, workflow=workflow, step=step)
        except Exception as exc:
            self._fail_step(run=run, step=step, exc=exc)

    def _complete_step(self, run: WorkflowRun, workflow, step: WorkflowStep) -> None:
        step.status = StepStatus.COMPLETED
        step.completed_at = step.completed_at or utc_now()
        next_step_id = workflow.next_step_id(step.step_id)
        run.current_step_id = next_step_id
        run.status = WorkflowStatus.RUNNING if next_step_id else WorkflowStatus.COMPLETED
        run.updated_at = utc_now()
        self._checkpoint(run, step.step_id)
        if run.status == WorkflowStatus.COMPLETED:
            self._complete_run(task=self._get_task(run.task_id), run=run)
        else:
            self.workflow_store.save_run(run)

    def _fail_step(self, run: WorkflowRun, step: WorkflowStep, exc: Exception) -> None:
        step.error = str(exc)
        self.trace_store.append(
            run,
            TraceEventType.STEP_FAILED,
            step_id=step.step_id,
            agent_name=step.agent_name,
            observation=step.error,
        )

        if step.retry_count < step.max_retries:
            step.retry_count += 1
            step.status = StepStatus.RETRYING
            run.status = WorkflowStatus.RETRYING
            run.current_step_id = step.step_id
            run.updated_at = utc_now()
            self.workflow_store.save_run(run)
            return

        step.status = StepStatus.FAILED
        run.status = WorkflowStatus.FAILED
        run.current_step_id = step.step_id
        run.error = step.error
        run.updated_at = utc_now()
        self.trace_store.append(
            run,
            TraceEventType.RUN_FAILED,
            step_id=step.step_id,
            agent_name=step.agent_name,
            observation=step.error,
        )
        self.workflow_store.save_run(run)

    def _checkpoint(self, run: WorkflowRun, step_id: str) -> None:
        checkpoint = self.checkpoint_store.create(run=run, step_id=step_id)
        self.trace_store.append(
            run,
            TraceEventType.CHECKPOINT_CREATED,
            step_id=step_id,
            observation=f"Checkpoint created: {checkpoint.checkpoint_id}",
            payload=checkpoint.model_dump(by_alias=True, mode="json"),
        )
        self.workflow_store.save_run(run)

    def _complete_run(self, task: AgentTask, run: WorkflowRun) -> None:
        run.status = WorkflowStatus.COMPLETED
        run.current_step_id = None
        run.output = self.orchestrator.compose_final_output(run)
        run.updated_at = utc_now()
        task.status = WorkflowStatus.COMPLETED
        task.updated_at = utc_now()
        self.trace_store.append(
            run,
            TraceEventType.RUN_COMPLETED,
            observation="Workflow run completed.",
            payload=run.output,
        )
        self.workflow_store.save_task(task)
        self.workflow_store.save_run(run)

    def _get_task(self, task_id: str) -> AgentTask:
        try:
            return self.workflow_store.get_task(task_id)
        except KeyError as exc:
            raise KeyError(f"task not found: {task_id}") from exc

    def _get_run(self, run_id: str) -> WorkflowRun:
        try:
            return self.workflow_store.get_run(run_id)
        except KeyError as exc:
            raise KeyError(f"workflow run not found: {run_id}") from exc

    def _resolve_workflow(self, task: AgentTask, workflow_id: Optional[str]):
        if workflow_id:
            return self.workflow_registry.get(workflow_id)
        if task.recommended_workflow:
            return self.workflow_registry.get(task.recommended_workflow)
        recommended = self.workflow_registry.recommend(task.domain, task.intent)
        if recommended:
            task.recommended_workflow = recommended.workflow_id
            return recommended
        raise KeyError(f"no workflow available for domain={task.domain}, intent={task.intent}")


def build_default_runtime() -> WorkflowRuntime:
    """Build the default AgentOS Core runtime with installed packs."""

    agent_registry = AgentRegistry()
    workflow_registry = WorkflowRegistry()
    register_installed_packs(agent_registry=agent_registry, workflow_registry=workflow_registry)
    workflow_store_path = os.getenv("AGENTOS_WORKFLOW_DB_PATH", "").strip()
    workflow_store = SQLiteWorkflowStore(workflow_store_path) if workflow_store_path else MemoryWorkflowStore()
    return WorkflowRuntime(
        agent_registry=agent_registry,
        workflow_registry=workflow_registry,
        workflow_store=workflow_store,
    )
