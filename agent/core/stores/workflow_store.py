from abc import ABC, abstractmethod
from typing import Iterable

from core.types import AgentTask, WorkflowRun


class WorkflowStore(ABC):
    """Persistence seam for AgentTask and WorkflowRun state."""

    @abstractmethod
    def save_task(self, task: AgentTask) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_task(self, task_id: str) -> AgentTask:
        raise NotImplementedError

    @abstractmethod
    def save_run(self, run: WorkflowRun) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_run(self, run_id: str) -> WorkflowRun:
        raise NotImplementedError

    @abstractmethod
    def list_runs(self) -> Iterable[WorkflowRun]:
        raise NotImplementedError
