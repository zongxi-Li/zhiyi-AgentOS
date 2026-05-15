from typing import Dict, Iterable

from core.stores.workflow_store import WorkflowStore
from core.types import AgentTask, WorkflowRun


class MemoryWorkflowStore(WorkflowStore):
    """In-memory WorkflowStore adapter for local development and tests."""

    def __init__(self):
        self._tasks: Dict[str, AgentTask] = {}
        self._runs: Dict[str, WorkflowRun] = {}

    def save_task(self, task: AgentTask) -> None:
        self._tasks[task.task_id] = task

    def get_task(self, task_id: str) -> AgentTask:
        try:
            return self._tasks[task_id]
        except KeyError as exc:
            raise KeyError(f"task not found: {task_id}") from exc

    def save_run(self, run: WorkflowRun) -> None:
        self._runs[run.run_id] = run

    def get_run(self, run_id: str) -> WorkflowRun:
        try:
            return self._runs[run_id]
        except KeyError as exc:
            raise KeyError(f"workflow run not found: {run_id}") from exc

    def list_runs(self) -> Iterable[WorkflowRun]:
        return tuple(self._runs.values())
