from dataclasses import dataclass, field
from typing import Any, Dict

from agentos.core.types import WorkflowRun, StepStatus


@dataclass
class WorkflowMemory:
    """Workflow-scoped context passed from one Agent step to the next."""

    run_id: str
    task_input: Dict[str, Any] = field(default_factory=dict)
    observations: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_run(cls, run: WorkflowRun) -> "WorkflowMemory":
        observations = {
            step.step_id: dict(step.output)
            for step in run.steps
            if step.status in {StepStatus.COMPLETED, StepStatus.WAITING_REVIEW} and step.output
        }
        return cls(run_id=run.run_id, task_input=dict(run.input), observations=observations)

    def record(self, step_id: str, output: Dict[str, Any]) -> None:
        self.observations[step_id] = dict(output)
