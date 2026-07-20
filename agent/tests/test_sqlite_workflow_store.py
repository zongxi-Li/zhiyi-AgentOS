from datetime import datetime, timezone
import sqlite3

from agentos.core.models.types import AgentTask, WorkflowRun, WorkflowStatus, WorkflowStep
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
        runtimeEngine="acg",
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


def test_sqlite_workflow_store_queries_tasks_and_runs_with_filters_and_pagination(tmp_path):
    store = SQLiteWorkflowStore(tmp_path / "workflow.db")

    chat_task = AgentTask(
        title="Chat案件分析",
        domain="legal",
        intent="case_analysis",
        input={"source": "chat", "caseText": "聊天升级"},
    )
    chat_task.status = WorkflowStatus.COMPLETED
    chat_task.created_at = datetime(2026, 5, 15, 9, 0, tzinfo=timezone.utc)
    chat_task.updated_at = chat_task.created_at
    store.save_task(chat_task)

    workbench_task = AgentTask(
        title="Workbench合同审查",
        domain="legal",
        intent="contract_review",
        input={"source": "workbench", "caseText": "工作台发起"},
    )
    workbench_task.status = WorkflowStatus.RUNNING
    workbench_task.created_at = datetime(2026, 5, 15, 10, 0, tzinfo=timezone.utc)
    workbench_task.updated_at = workbench_task.created_at
    store.save_task(workbench_task)

    chat_run = WorkflowRun(
        taskId=chat_task.task_id,
        workflowId="legal_case_analysis_v1",
        domain="legal",
        runtimeEngine="acg",
        input={"source": "chat", "caseText": "聊天升级"},
    )
    chat_run.status = WorkflowStatus.COMPLETED
    chat_run.created_at = datetime(2026, 5, 15, 9, 1, tzinfo=timezone.utc)
    chat_run.updated_at = chat_run.created_at
    store.save_run(chat_run)

    workbench_run = WorkflowRun(
        taskId=workbench_task.task_id,
        workflowId="legal_contract_review_v1",
        domain="legal",
        runtimeEngine="acg",
        input={"source": "workbench", "caseText": "工作台发起"},
    )
    workbench_run.status = WorkflowStatus.RUNNING
    workbench_run.created_at = datetime(2026, 5, 15, 10, 1, tzinfo=timezone.utc)
    workbench_run.updated_at = workbench_run.created_at
    store.save_run(workbench_run)

    task_page = store.list_tasks(status=WorkflowStatus.RUNNING, domain="legal", source="workbench")
    assert task_page.total == 1
    assert [task.task_id for task in task_page.items] == [workbench_task.task_id]

    run_page = store.list_runs(status=WorkflowStatus.RUNNING, workflow_id="legal_contract_review_v1", source="workbench")
    assert run_page.total == 1
    assert [run.run_id for run in run_page.items] == [workbench_run.run_id]

    paged_runs = store.list_runs(page=2, page_size=1)
    assert paged_runs.total == 2
    assert paged_runs.page == 2
    assert paged_runs.page_size == 1
    assert [run.run_id for run in paged_runs.items] == [chat_run.run_id]


def test_sqlite_workflow_store_enables_wal_and_verified_backup(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTOS_SQLITE_BUSY_TIMEOUT_MS", "4321")
    source = tmp_path / "workflow.db"
    backup = tmp_path / "backup" / "workflow.db"
    store = SQLiteWorkflowStore(source)
    task = AgentTask(title="持久化测试", domain="legal", intent="contract_review")
    store.save_task(task)
    result = store.backup_to(backup)
    with sqlite3.connect(source) as conn:
        assert conn.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
    assert store.busy_timeout_ms == 4321
    assert result["integrity"] == "ok"
    assert result["taskCount"] == 1
    assert result["runCount"] == 0
    assert SQLiteWorkflowStore(backup).get_task(task.task_id).title == "持久化测试"
