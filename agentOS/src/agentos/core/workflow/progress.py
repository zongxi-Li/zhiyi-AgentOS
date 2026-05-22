"""Workflow progress calculation for tasks and runs."""

from __future__ import annotations

from collections import Counter
from typing import Optional

from pydantic import Field

from agentos.core.models.types import (
    AgentTask,
    CoreModel,
    StepStatus,
    WorkflowDefinition,
    WorkflowRun,
    WorkflowStatus,
)


class WorkflowProgress(CoreModel):
    """Snapshot of progress across a task, workflow run, and workflow definition."""

    task_id: str = Field(alias="taskId")
    run_id: Optional[str] = Field(default=None, alias="runId")
    workflow_id: Optional[str] = Field(default=None, alias="workflowId")
    status: WorkflowStatus = WorkflowStatus.PENDING
    total_steps: int = Field(default=0, alias="totalSteps")
    pending_steps: int = Field(default=0, alias="pendingSteps")
    running_steps: int = Field(default=0, alias="runningSteps")
    waiting_review_steps: int = Field(default=0, alias="waitingReviewSteps")
    retrying_steps: int = Field(default=0, alias="retryingSteps")
    failed_steps: int = Field(default=0, alias="failedSteps")
    completed_steps: int = Field(default=0, alias="completedSteps")
    cancelled_steps: int = Field(default=0, alias="cancelledSteps")
    current_step_id: Optional[str] = Field(default=None, alias="currentStepId")
    progress: float = 0.0
    percentage: float = 0.0


class ProgressCalculator:
    """Calculates user-facing progress from canonical workflow state."""

    def calculate(
        self,
        *,
        task: AgentTask,
        run: WorkflowRun | None = None,
        workflow: WorkflowDefinition | None = None,
    ) -> WorkflowProgress:
        status = run.status if run is not None else task.status
        workflow_id = self._workflow_id(task=task, run=run, workflow=workflow)
        step_statuses = self._step_statuses(run=run, workflow=workflow)
        counts = Counter(step_statuses)
        total_steps = len(step_statuses)

        progress_units = counts[StepStatus.COMPLETED] + counts[StepStatus.WAITING_REVIEW]
        if status == WorkflowStatus.COMPLETED and total_steps:
            progress_units = total_steps

        progress = round(progress_units / total_steps, 4) if total_steps else 0.0
        percentage = round(progress * 100, 2)

        return WorkflowProgress(
            taskId=task.task_id,
            runId=run.run_id if run is not None else None,
            workflowId=workflow_id,
            status=status,
            totalSteps=total_steps,
            pendingSteps=counts[StepStatus.PENDING],
            runningSteps=counts[StepStatus.RUNNING],
            waitingReviewSteps=counts[StepStatus.WAITING_REVIEW],
            retryingSteps=counts[StepStatus.RETRYING],
            failedSteps=counts[StepStatus.FAILED],
            completedSteps=counts[StepStatus.COMPLETED],
            cancelledSteps=counts[StepStatus.CANCELLED],
            currentStepId=run.current_step_id if run is not None else None,
            progress=progress,
            percentage=percentage,
        )

    def _workflow_id(
        self,
        *,
        task: AgentTask,
        run: WorkflowRun | None,
        workflow: WorkflowDefinition | None,
    ) -> str | None:
        if run is not None:
            return run.workflow_id
        if workflow is not None:
            return workflow.workflow_id
        return task.recommended_workflow

    def _step_statuses(
        self,
        *,
        run: WorkflowRun | None,
        workflow: WorkflowDefinition | None,
    ) -> list[StepStatus]:
        if run is not None:
            return [step.status for step in run.steps]
        if workflow is not None:
            return [StepStatus.PENDING for _ in workflow.steps]
        return []


__all__ = ["ProgressCalculator", "WorkflowProgress"]
