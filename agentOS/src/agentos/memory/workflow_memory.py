"""AgentOS Core 的记忆 workflow_memory 模块，管理工作流步骤之间的上下文传递。"""


from dataclasses import dataclass, field
from typing import Any, Dict

from agentos.core.models.types import WorkflowRun, StepStatus


@dataclass
class WorkflowMemory:
    """在 Agent 步骤之间传递的工作流级上下文。"""

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
