from __future__ import annotations

from typing import Any, Dict

from agentos.core.governance.checkpoint import CheckpointStore
from agentos.core.governance.trace import TraceStore
from agentos.core.models.types import (
    AgentTask,
    StepStatus,
    TraceEventType,
    WorkflowRun,
    WorkflowStatus,
    utc_now,
)
from agentos.stores.workflow_store import WorkflowStore


class ContractReviewRunProjector:
    """Projects LangGraph state back into AgentOS WorkflowRun governance objects."""

    def __init__(
        self,
        *,
        workflow_store: WorkflowStore,
        trace_store: TraceStore,
        checkpoint_store: CheckpointStore,
    ):
        self.workflow_store = workflow_store
        self.trace_store = trace_store
        self.checkpoint_store = checkpoint_store
        self._synced_trace_counts: Dict[str, int] = {}
        self._checkpointed_steps: Dict[str, set[str]] = {}

    def project(self, *, task: AgentTask, run: WorkflowRun, state: Dict[str, Any]) -> WorkflowRun:
        artifacts = state.get("artifacts") if isinstance(state.get("artifacts"), dict) else {}
        steps = state.get("steps") if isinstance(state.get("steps"), dict) else {}

        for step in run.steps:
            step_state = steps.get(step.step_id, {}) if isinstance(steps.get(step.step_id), dict) else {}
            status = step_state.get("status")
            if status:
                step.status = StepStatus(status)
            output = step_state.get("output")
            if isinstance(output, dict):
                step.output = output
            elif isinstance(artifacts.get(step.step_id), dict):
                step.output = dict(artifacts[step.step_id])
            if step.status in {StepStatus.COMPLETED, StepStatus.WAITING_REVIEW}:
                step.started_at = step.started_at or utc_now()
            if step.status == StepStatus.COMPLETED:
                step.completed_at = step.completed_at or utc_now()

        run.status = WorkflowStatus(state.get("status") or WorkflowStatus.RUNNING.value)
        run.current_step_id = state.get("current_step")
        if run.status == WorkflowStatus.COMPLETED:
            run.current_step_id = None
        run.output = {
            "final_answer": state.get("report_markdown") or "",
            "artifacts": artifacts,
        }
        run.error = state.get("error")
        run.updated_at = utc_now()

        self._sync_traces(run, state.get("traces", []))
        self._sync_checkpoints(run)

        task.status = run.status
        task.updated_at = utc_now()
        if run.status == WorkflowStatus.COMPLETED:
            self.trace_store.append(
                run=run,
                event_type=TraceEventType.RUN_COMPLETED,
                observation="LangGraph workflow completed.",
                payload=run.output,
            )
        self.workflow_store.save_task(task)
        self.workflow_store.save_run(run)
        return run

    def _sync_traces(self, run: WorkflowRun, traces: Any) -> None:
        if not isinstance(traces, list):
            return
        start = self._synced_trace_counts.get(run.run_id, 0)
        for index, item in enumerate(traces[start:], start=start):
            if not isinstance(item, dict):
                continue
            event_type = TraceEventType(item.get("eventType") or TraceEventType.AGENT_CALLED.value)
            payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}
            payload["langgraphTraceIndex"] = index
            self.trace_store.append(
                run=run,
                event_type=event_type,
                step_id=item.get("stepId"),
                agent_name=item.get("agentName"),
                observation=str(item.get("observation") or ""),
                payload=payload,
            )
        self._synced_trace_counts[run.run_id] = len(traces)

    def _sync_checkpoints(self, run: WorkflowRun) -> None:
        checkpointed = self._checkpointed_steps.setdefault(run.run_id, set())
        for step in run.steps:
            if step.step_id in checkpointed:
                continue
            if step.status not in {StepStatus.COMPLETED, StepStatus.WAITING_REVIEW}:
                continue
            self.checkpoint_store.create(run, step.step_id)
            checkpointed.add(step.step_id)
