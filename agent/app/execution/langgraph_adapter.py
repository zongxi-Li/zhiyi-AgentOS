"""LangGraph execution adapter for the Python Agent application layer."""

from __future__ import annotations

from typing import Any

from agentos.core.models.types import AgentTask, ReviewDecision, WorkflowDefinition, WorkflowRun

from app.execution.langgraph_registry import LangGraphImplementationRegistry, get_default_langgraph_registry


class LangGraphAdapter:
    """Runs app-layer LangGraph workflows while preserving AgentOS governance objects."""

    def __init__(
        self,
        *,
        runtime: Any,
        implementation_id: str,
        registry: LangGraphImplementationRegistry | None = None,
    ):
        self.runtime = runtime
        self.implementation_id = implementation_id
        self.registry = registry or get_default_langgraph_registry()
        self._delegate: Any | None = None

    @property
    def delegate(self) -> Any:
        if self._delegate is None:
            self._delegate = self.registry.create(
                self.implementation_id,
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
