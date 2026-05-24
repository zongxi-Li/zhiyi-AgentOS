"""Execution adapter protocols and native runtime adapter for AgentOS Core."""

from __future__ import annotations

from typing import Any, Protocol

from agentos.core.models.types import AgentTask, ReviewDecision, WorkflowDefinition, WorkflowRun


class ExecutionAdapter(Protocol):
    async def start(self, *, task: AgentTask, run: WorkflowRun, workflow: WorkflowDefinition) -> WorkflowRun:
        ...

    async def apply_review(self, decision: ReviewDecision) -> WorkflowRun:
        ...


class ExecutionAdapterFactory(Protocol):
    def __call__(
        self,
        *,
        runtime: Any,
        workflow: WorkflowDefinition,
        implementation_id: str,
    ) -> ExecutionAdapter:
        ...


class NativeWorkflowAdapter:
    """Runs regular YAML step workflows through the built-in Orchestrator."""

    def __init__(self, runtime: Any):
        self.runtime = runtime

    async def start(self, *, task: AgentTask, run: WorkflowRun, workflow: WorkflowDefinition) -> WorkflowRun:
        return await self.runtime._start_native(task=task, run=run, workflow=workflow)

    async def apply_review(self, decision: ReviewDecision) -> WorkflowRun:
        return await self.runtime._apply_native_review(decision)
