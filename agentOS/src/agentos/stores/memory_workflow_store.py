"""AgentOS Core 的存储 memory_workflow_store 模块，管理任务和运行记录的持久化边界。"""


from __future__ import annotations

from typing import Dict

from agentos.core.models.types import AgentTask, WorkflowRun, WorkflowStatus
from agentos.stores.workflow_store import WorkflowStore, WorkflowStorePage, paginate_items, status_value


class MemoryWorkflowStore(WorkflowStore):
    """面向本地开发和测试的内存 WorkflowStore 适配器。"""

    def __init__(self):
        self._tasks: Dict[str, AgentTask] = {}
        self._runs: Dict[str, WorkflowRun] = {}
        self._terminal_run_statuses: Dict[str, WorkflowStatus] = {}

    def save_task(self, task: AgentTask) -> None:
        self._tasks[task.task_id] = task

    def get_task(self, task_id: str) -> AgentTask:
        try:
            return self._tasks[task_id]
        except KeyError as exc:
            raise KeyError(f"task not found: {task_id}") from exc

    def save_run(self, run: WorkflowRun) -> None:
        existing = self._runs.get(run.run_id)
        terminal_status = self._terminal_run_statuses.get(run.run_id)
        if terminal_status is not None and _reject_terminal_status_overwrite(terminal_status, run.status):
            return
        if existing is not None and _reject_terminal_overwrite(existing, run):
            return
        if run.status in {
            WorkflowStatus.COMPLETED,
            WorkflowStatus.FAILED,
            WorkflowStatus.CANCELLED,
        }:
            self._terminal_run_statuses[run.run_id] = run.status
        elif terminal_status == WorkflowStatus.FAILED and run.status == WorkflowStatus.RETRYING:
            self._terminal_run_statuses.pop(run.run_id, None)
        self._runs[run.run_id] = run.model_copy(deep=True)

    def get_run(self, run_id: str) -> WorkflowRun:
        try:
            return self._runs[run_id].model_copy(deep=True)
        except KeyError as exc:
            raise KeyError(f"workflow run not found: {run_id}") from exc

    def list_tasks(
        self,
        *,
        status: WorkflowStatus | str | None = None,
        domain: str | None = None,
        source: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> WorkflowStorePage[AgentTask]:
        expected_status = status_value(status)
        tasks = [
            task.model_copy(deep=True)
            for task in self._tasks.values()
            if _matches_task(task, status=expected_status, domain=domain, source=source)
        ]
        tasks.sort(key=lambda task: (task.created_at, task.task_id), reverse=True)
        return paginate_items(tasks, page=page, page_size=page_size)

    def list_runs(
        self,
        *,
        status: WorkflowStatus | str | None = None,
        domain: str | None = None,
        workflow_id: str | None = None,
        source: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> WorkflowStorePage[WorkflowRun]:
        expected_status = status_value(status)
        runs = [
            run.model_copy(deep=True)
            for run in self._runs.values()
            if _matches_run(
                run,
                status=expected_status,
                domain=domain,
                workflow_id=workflow_id,
                source=source,
            )
        ]
        runs.sort(key=lambda run: (run.created_at, run.run_id), reverse=True)
        return paginate_items(runs, page=page, page_size=page_size)

    def list_non_terminal_runs(self, *, limit: int = 200) -> tuple[WorkflowRun, ...]:
        terminal = {
            WorkflowStatus.COMPLETED,
            WorkflowStatus.FAILED,
            WorkflowStatus.CANCELLED,
        }
        runs = [run.model_copy(deep=True) for run in self._runs.values() if run.status not in terminal]
        runs.sort(key=lambda run: (run.updated_at, run.run_id), reverse=True)
        return tuple(runs[: max(1, limit)])

    def find_run_by_idempotency_key(self, idempotency_key: str) -> WorkflowRun | None:
        matches = [
            run.model_copy(deep=True)
            for run in self._runs.values()
            if run.idempotency_key == idempotency_key
        ]
        if not matches:
            return None
        return max(matches, key=lambda run: (run.created_at, run.run_id))


def _matches_task(task: AgentTask, *, status: str | None, domain: str | None, source: str | None) -> bool:
    if status is not None and task.status.value != status:
        return False
    if domain is not None and task.domain != domain:
        return False
    if source is not None and task.input.get("source") != source:
        return False
    return True


def _matches_run(
    run: WorkflowRun,
    *,
    status: str | None,
    domain: str | None,
    workflow_id: str | None,
    source: str | None,
) -> bool:
    if status is not None and run.status.value != status:
        return False
    if domain is not None and run.domain != domain:
        return False
    if workflow_id is not None and run.workflow_id != workflow_id:
        return False
    if source is not None and run.input.get("source") != source:
        return False
    return True


def _reject_terminal_overwrite(existing: WorkflowRun, incoming: WorkflowRun) -> bool:
    terminal = {
        WorkflowStatus.COMPLETED,
        WorkflowStatus.FAILED,
        WorkflowStatus.CANCELLED,
    }
    if existing.status == WorkflowStatus.FAILED and incoming.status == WorkflowStatus.RETRYING:
        return False
    if existing.status in terminal and incoming.status != existing.status:
        return True
    return existing.status in terminal and incoming.updated_at < existing.updated_at


def _reject_terminal_status_overwrite(
    existing: WorkflowStatus,
    incoming: WorkflowStatus,
) -> bool:
    if existing == WorkflowStatus.FAILED and incoming == WorkflowStatus.RETRYING:
        return False
    return incoming != existing
