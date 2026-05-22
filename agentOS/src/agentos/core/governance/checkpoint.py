"""AgentOS Core 的 checkpoint 模块，提供运行时控制、状态、Trace、审核或治理能力。"""


from typing import Any, Dict, List
from agentos.core.models.types import Checkpoint, WorkflowRun


class CheckpointStore:
    """创建并查询内存中的工作流检查点。"""

    def create(self, run: WorkflowRun, step_id: str) -> Checkpoint:
        state_snapshot: Dict[str, Any] = {
            "runId": run.run_id,
            "taskId": run.task_id,
            "workflowId": run.workflow_id,
            "domain": run.domain,
            "status": run.status.value,
            "currentStepId": run.current_step_id,
            "reviewMode": run.review_mode,
            "input": run.input,
            "output": run.output,
            "steps": [step.model_dump(by_alias=True, mode="json") for step in run.steps],
        }
        checkpoint = Checkpoint(
            runId=run.run_id,
            stepId=step_id,
            stateSnapshot=state_snapshot,
            outputSnapshot=dict(run.get_step(step_id).output),
            canResume=True,
        )
        run.checkpoints.append(checkpoint)
        return checkpoint

    def find(self, run: WorkflowRun, checkpoint_id: str) -> Checkpoint:
        for checkpoint in run.checkpoints:
            if checkpoint.checkpoint_id == checkpoint_id:
                return checkpoint
        raise KeyError(f"checkpoint not found: {checkpoint_id}")

    def list(self, run: WorkflowRun) -> List[Checkpoint]:
        return sorted(run.checkpoints, key=lambda checkpoint: (checkpoint.created_at, checkpoint.checkpoint_id))
