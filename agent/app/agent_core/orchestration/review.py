from app.agent_core.orchestration.types import ReviewDecision, TraceEventType, WorkflowRun
from app.agent_core.orchestration.trace import TraceStore


class ReviewManager:
    """Records human review decisions as auditable trace events."""

    def __init__(self, trace_store: TraceStore):
        self.trace_store = trace_store

    def record(self, run: WorkflowRun, decision: ReviewDecision) -> None:
        self.trace_store.append(
            run=run,
            event_type=TraceEventType.REVIEW_DECIDED,
            step_id=decision.step_id,
            observation=f"Review decision: {decision.decision.value}",
            payload=decision.model_dump(by_alias=True, mode="json"),
        )
