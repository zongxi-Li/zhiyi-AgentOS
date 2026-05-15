from datetime import datetime, timezone

from agentos.core.types import AgentTask, WorkflowRun, WorkflowStatus, WorkflowStep
from agentos.stores.sqlite_workflow_store import SQLiteWorkflowStore


def test_sqlite_workflow_store_persists_tasks_and_runs(tmp_path):
    store = SQLiteWorkflowStore(tmp_path / "workflow.db")

    task = AgentTask(
        title="合同审查",
        domain="legal",
        intent="contract_review",
        input={"caseText": "合同逾期交付"},
    )
    task.updated_at = datetime(2026, 5, 15, tzinfo=timezone.utc)
    store.save_task(task)

    run = WorkflowRun(
        taskId=task.task_id,
        workflowId="legal_contract_review_v1",
        domain="legal",
        currentStepId="case_intake",
        input={"caseText": "合同逾期交付"},
        steps=[
            WorkflowStep(
                stepId="case_intake",
                name="Case Intake",
                agentName="case_intake",
            )
        ],
    )
    run.status = WorkflowStatus.RUNNING
    run.updated_at = datetime(2026, 5, 15, tzinfo=timezone.utc)
    store.save_run(run)

    reopened = SQLiteWorkflowStore(tmp_path / "workflow.db")
    loaded_task = reopened.get_task(task.task_id)
    loaded_run = reopened.get_run(run.run_id)

    assert loaded_task.title == "合同审查"
    assert loaded_task.input["caseText"] == "合同逾期交付"
    assert loaded_run.workflow_id == "legal_contract_review_v1"
    assert loaded_run.current_step_id == "case_intake"
    assert loaded_run.status == WorkflowStatus.RUNNING
    assert [item.run_id for item in reopened.list_runs()] == [run.run_id]
