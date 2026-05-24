"""Application runtime wiring for AgentOS execution adapters."""

from __future__ import annotations

from typing import Any

from agentos.core.models.types import WorkflowDefinition
from agentos.core.runtime import WorkflowRuntime, build_default_runtime as build_core_default_runtime

from app.execution.langgraph_adapter import LangGraphAdapter
from app.execution.langgraph_registry import get_default_langgraph_registry


def build_langgraph_adapter(
    *,
    runtime: Any,
    workflow: WorkflowDefinition,
    implementation_id: str,
):
    return LangGraphAdapter(
        runtime=runtime,
        implementation_id=implementation_id,
        registry=get_default_langgraph_registry(),
    )


def configure_execution_adapters(runtime: WorkflowRuntime) -> WorkflowRuntime:
    runtime.register_execution_adapter("langgraph", build_langgraph_adapter)
    return runtime


def build_default_runtime() -> WorkflowRuntime:
    return configure_execution_adapters(build_core_default_runtime())
