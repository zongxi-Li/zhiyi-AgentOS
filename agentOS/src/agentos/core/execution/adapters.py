"""Execution adapters keep workflow engines behind the AgentOS Core runtime."""

from __future__ import annotations

from typing import Any, Protocol

from agentos.core.models.types import AgentTask, ReviewDecision, WorkflowDefinition, WorkflowRun


class ExecutionAdapter(Protocol):
    async def start(self, *, task: AgentTask, run: WorkflowRun, workflow: WorkflowDefinition) -> WorkflowRun:
        ...

    async def apply_review(self, decision: ReviewDecision) -> WorkflowRun:
        ...


class NativeWorkflowAdapter:
    """Runs regular YAML step workflows through the built-in Orchestrator."""

    def __init__(self, runtime: Any):
        self.runtime = runtime

    async def start(self, *, task: AgentTask, run: WorkflowRun, workflow: WorkflowDefinition) -> WorkflowRun:
        return await self.runtime._start_native(task=task, run=run, workflow=workflow)

    async def apply_review(self, decision: ReviewDecision) -> WorkflowRun:
        return await self.runtime._apply_native_review(decision)


class LangGraphAdapter:
    """Runs workflows implemented by LangGraph while preserving AgentOS governance objects."""

    def __init__(self, *, runtime: Any, implementation_id: str):
        self.runtime = runtime
        self.implementation_id = implementation_id
        self._delegate: Any | None = None

    @property
    def delegate(self) -> Any:
        if self._delegate is None:
            if self.implementation_id != "legal_contract_review_stategraph_v1":
                raise ValueError(f"Unsupported LangGraph implementation: {self.implementation_id}")
            from app.graphs.legal_contract_review_stategraph import LegalContractReviewStateGraphRuntime

            self._delegate = LegalContractReviewStateGraphRuntime(
                workflow_store=self.runtime.workflow_store,
                trace_store=self.runtime.trace_store,
                checkpoint_store=self.runtime.checkpoint_store,
                review_manager=self.runtime.review_manager,
            )
        return self._delegate

    async def start(self, *, task: AgentTask, run: WorkflowRun, workflow: WorkflowDefinition) -> WorkflowRun:
        return await self.delegate.start(task=task, run=run, workflow=workflow)

    async def apply_review(self, decision: ReviewDecision) -> WorkflowRun:
        return await self.delegate.apply_review(decision)
