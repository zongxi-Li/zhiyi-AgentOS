"""Shared lifecycle enums for AgentOS core models and projections."""

from enum import Enum


class WorkflowProgressPhase(str, Enum):
    """Persisted and projected phases of a workflow run lifecycle."""

    UNDERSTANDING = "understanding"
    PLANNING = "planning"
    GRAPH_BUILDING = "graph_building"
    EXECUTING = "executing"
    RECOVERY = "recovery"
    REVIEW = "review"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


__all__ = ["WorkflowProgressPhase"]
