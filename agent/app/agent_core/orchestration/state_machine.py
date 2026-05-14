from enum import Enum
from typing import TypeVar

from app.agent_core.orchestration.types import StepStatus, WorkflowStatus

StatusT = TypeVar("StatusT", WorkflowStatus, StepStatus)


class InvalidStateTransition(ValueError):
    """Raised when a workflow or step attempts an illegal status transition."""


class StateMachine:
    """Shared state machine for workflow runs and steps."""

    _transitions = {
        "pending": {"planning", "running", "cancelled"},
        "planning": {"running", "failed", "cancelled"},
        "running": {"waiting_review", "retrying", "failed", "completed", "cancelled"},
        "waiting_review": {"running", "retrying", "failed", "completed", "cancelled"},
        "retrying": {"running", "failed", "cancelled"},
        "failed": {"retrying", "cancelled"},
        "completed": set(),
        "cancelled": set(),
    }

    def can_transition(self, current: Enum, target: Enum) -> bool:
        if current == target:
            return True
        return target.value in self._transitions.get(current.value, set())

    def transition(self, current: StatusT, target: StatusT) -> StatusT:
        if not self.can_transition(current, target):
            raise InvalidStateTransition(f"illegal transition: {current.value} -> {target.value}")
        return target
