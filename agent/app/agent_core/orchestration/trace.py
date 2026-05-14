from typing import Any, Dict, Optional

from app.agent_core.orchestration.types import TraceEvent, TraceEventType, WorkflowRun


class TraceStore:
    """In-memory trace writer bound to WorkflowRun objects."""

    def append(
        self,
        run: WorkflowRun,
        event_type: TraceEventType,
        observation: str = "",
        step_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        duration_ms: int = 0,
    ) -> TraceEvent:
        event = TraceEvent(
            runId=run.run_id,
            stepId=step_id,
            agentName=agent_name,
            eventType=event_type,
            observation=observation,
            payload=payload or {},
            durationMs=max(0, int(duration_ms)),
        )
        run.trace.append(event)
        return event
