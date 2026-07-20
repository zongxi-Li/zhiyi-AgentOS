import pytest

from agentos.core.models.types import (
    AgentTask,
    StepStatus,
    WorkflowDefinition,
    WorkflowRun,
    WorkflowStatus,
    WorkflowStep,
    WorkflowStepDefinition,
)
from agentos.core.workflow.progress import ProgressCalculator
from agentos.core.workflow.registry import WorkflowRegistry
from agentos.core.workflow.task_manager import TaskManager
from agentos.stores.memory_workflow_store import MemoryWorkflowStore


def _workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        workflowId="legal_contract_review_v1",
        name="Legal Contract Review",
        domain="legal",
        intent="contract_review",
        runtimeEngine="acg",
        steps=[
            WorkflowStepDefinition(stepId="risk", name="Risk", agentName="risk"),
            WorkflowStepDefinition(stepId="review", name="Review", agentName="review", reviewRequired=True),
            WorkflowStepDefinition(stepId="draft", name="Draft", agentName="draft"),
        ],
    )


def test_progress_calculator_counts_run_step_statuses_and_percentage():
    workflow = _workflow()
    task = AgentTask(
        title="合同审查",
        domain="legal",
        intent="contract_review",
        recommendedWorkflow=workflow.workflow_id,
    )
    run = WorkflowRun(
        taskId=task.task_id,
        workflowId=workflow.workflow_id,
        domain="legal",
        runtimeEngine="acg",
        status=WorkflowStatus.WAITING_REVIEW,
        currentStepId="review",
        steps=[
            WorkflowStep(stepId="risk", name="Risk", agentName="risk", status=StepStatus.COMPLETED),
            WorkflowStep(stepId="review", name="Review", agentName="review", status=StepStatus.WAITING_REVIEW),
            WorkflowStep(stepId="draft", name="Draft", agentName="draft", status=StepStatus.PENDING),
        ],
    )

    progress = ProgressCalculator().calculate(task=task, run=run, workflow=workflow)

    assert progress.task_id == task.task_id
    assert progress.run_id == run.run_id
    assert progress.workflow_id == workflow.workflow_id
    assert progress.status == WorkflowStatus.WAITING_REVIEW
    assert progress.total_steps == 3
    assert progress.completed_steps == 1
    assert progress.waiting_review_steps == 1
    assert progress.pending_steps == 1
    assert progress.current_step_id == "review"
    assert progress.progress == pytest.approx(0.6667)
    assert progress.percentage == pytest.approx(66.67)


def test_task_manager_calculates_zero_progress_for_task_before_run_starts():
    registry = WorkflowRegistry()
    workflow = _workflow()
    registry.register(workflow)
    manager = TaskManager(workflow_store=MemoryWorkflowStore(), workflow_registry=registry)
    task = manager.create_task(title="合同审查", domain="legal", intent="contract_review")

    progress = manager.calculate_progress(task)

    assert progress.task_id == task.task_id
    assert progress.workflow_id == workflow.workflow_id
    assert progress.status == WorkflowStatus.PENDING
    assert progress.total_steps == 3
    assert progress.pending_steps == 3
    assert progress.completed_steps == 0
    assert progress.progress == 0
    assert progress.percentage == 0


def test_progress_calculator_handles_task_without_workflow_or_run():
    task = AgentTask(title="临时任务", domain="general", intent="general")

    progress = ProgressCalculator().calculate(task=task)

    assert progress.task_id == task.task_id
    assert progress.workflow_id is None
    assert progress.total_steps == 0
    assert progress.progress == 0
    assert progress.percentage == 0
