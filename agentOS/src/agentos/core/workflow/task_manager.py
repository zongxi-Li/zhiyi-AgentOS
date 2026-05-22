"""任务管理器，负责任务创建、工作流绑定和生命周期状态流转。"""


from __future__ import annotations

from typing import Any, Optional

from agentos.core.workflow.registry import WorkflowRegistry
from agentos.core.workflow.state_machine import StateMachine
from agentos.core.models.types import AgentTask, WorkflowDefinition, WorkflowStatus, utc_now
from agentos.stores.workflow_store import WorkflowStore, WorkflowStorePage


class TaskManager:
    """任务控制面服务，负责任务创建、工作流绑定和生命周期状态。"""

    def __init__(
        self,
        *,
        workflow_store: WorkflowStore,
        workflow_registry: WorkflowRegistry,
        state_machine: Optional[StateMachine] = None,
    ):
        self.workflow_store = workflow_store
        self.workflow_registry = workflow_registry
        self.state_machine = state_machine or StateMachine()

    def create_task(
        self,
        title: str,
        domain: str = "general",
        intent: str = "general",
        input: Optional[dict[str, Any]] = None,
        security_level: str = "internal",
        priority: str = "normal",
        *,
        role_type: Optional[str] = None,
        task_type: Optional[str] = None,
        workflow_id: Optional[str] = None,
    ) -> AgentTask:
        task_domain = self._first_nonblank(role_type, domain, default="general")
        task_intent = self._first_nonblank(task_type, intent, default="general")
        workflow = self._select_workflow(task_domain, task_intent, workflow_id)

        task = AgentTask(
            title=title,
            domain=task_domain,
            intent=task_intent,
            input=input or {},
            securityLevel=security_level,
            priority=priority,
            recommendedWorkflow=workflow.workflow_id if workflow else None,
        )
        self.workflow_store.save_task(task)
        return task

    def get_task(self, task_id: str) -> AgentTask:
        return self.workflow_store.get_task(task_id)

    def list_tasks(
        self,
        *,
        status: WorkflowStatus | str | None = None,
        domain: str | None = None,
        source: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> WorkflowStorePage[AgentTask]:
        return self.workflow_store.list_tasks(
            status=status,
            domain=domain,
            source=source,
            page=page,
            page_size=page_size,
        )

    def bind_workflow(self, task: AgentTask | str, workflow_id: Optional[str] = None) -> WorkflowDefinition:
        resolved_task = self._task(task)
        workflow = self._select_workflow(
            resolved_task.domain,
            resolved_task.intent,
            workflow_id or resolved_task.recommended_workflow,
        )
        if workflow is None:
            raise KeyError(
                f"workflow not found for domain={resolved_task.domain}, intent={resolved_task.intent}"
            )
        if resolved_task.recommended_workflow != workflow.workflow_id:
            resolved_task.recommended_workflow = workflow.workflow_id
            resolved_task.updated_at = utc_now()
            self.workflow_store.save_task(resolved_task)
        return workflow

    def mark_running(self, task: AgentTask | str) -> AgentTask:
        return self.transition(task, WorkflowStatus.RUNNING)

    def mark_waiting_review(self, task: AgentTask | str) -> AgentTask:
        return self.transition(task, WorkflowStatus.WAITING_REVIEW)

    def mark_retrying(self, task: AgentTask | str) -> AgentTask:
        return self.transition(task, WorkflowStatus.RETRYING)

    def mark_failed(self, task: AgentTask | str) -> AgentTask:
        return self.transition(task, WorkflowStatus.FAILED)

    def mark_completed(self, task: AgentTask | str) -> AgentTask:
        return self.transition(task, WorkflowStatus.COMPLETED)

    def mark_cancelled(self, task: AgentTask | str) -> AgentTask:
        return self.transition(task, WorkflowStatus.CANCELLED)

    def transition(self, task: AgentTask | str, status: WorkflowStatus | str) -> AgentTask:
        resolved_task = self._task(task)
        target = status if isinstance(status, WorkflowStatus) else WorkflowStatus(status)
        resolved_task.status = self.state_machine.transition(resolved_task.status, target)
        resolved_task.updated_at = utc_now()
        self.workflow_store.save_task(resolved_task)
        return resolved_task

    def _task(self, task: AgentTask | str) -> AgentTask:
        if isinstance(task, AgentTask):
            return task
        return self.workflow_store.get_task(task)

    def _select_workflow(
        self,
        domain: str,
        intent: str,
        workflow_id: Optional[str],
    ) -> Optional[WorkflowDefinition]:
        if workflow_id:
            return self.workflow_registry.get(workflow_id)
        return self.workflow_registry.recommend(domain=domain, intent=intent)

    @staticmethod
    def _first_nonblank(preferred: Optional[str], fallback: Optional[str], *, default: str) -> str:
        for value in (preferred, fallback):
            normalized = (value or "").strip()
            if normalized:
                return normalized
        return default


__all__ = ["TaskManager"]
