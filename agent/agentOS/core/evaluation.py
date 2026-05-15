from typing import Iterable

from agentos.core.types import WorkflowRun, WorkflowStatus


class WorkflowEvaluator:
    """Calculates simple workflow-level governance metrics."""

    def evaluate(self, runs: Iterable[WorkflowRun]) -> dict:
        items = list(runs)
        total = len(items)
        if total == 0:
            return {
                "total_runs": 0,
                "completion_rate": 0.0,
                "failure_rate": 0.0,
                "recovery_success_rate": 0.0,
            }

        completed = sum(1 for run in items if run.status == WorkflowStatus.COMPLETED)
        failed = sum(1 for run in items if run.status == WorkflowStatus.FAILED)
        recovered = sum(1 for run in items if run.recovery_count > 0 and run.status == WorkflowStatus.COMPLETED)
        recovery_attempts = sum(1 for run in items if run.recovery_count > 0)

        return {
            "total_runs": total,
            "completion_rate": round(completed / total, 4),
            "failure_rate": round(failed / total, 4),
            "recovery_success_rate": round(recovered / recovery_attempts, 4) if recovery_attempts else 0.0,
        }
