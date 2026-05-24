from __future__ import annotations

from typing import Any, Dict

from langgraph.types import Command

from agentos.core.governance.checkpoint import CheckpointStore
from agentos.core.governance.review import ReviewManager
from agentos.core.governance.trace import TraceStore
from agentos.core.models.types import (
    AgentTask,
    ReviewDecision,
    ReviewDecisionType,
    StepStatus,
    TraceEventType,
    WorkflowDefinition,
    WorkflowRun,
    WorkflowStatus,
    utc_now,
)
from agentos.stores.workflow_store import WorkflowStore
from app.graphs.contract_review.graph import build_contract_review_graph
from app.graphs.contract_review.projector import ContractReviewRunProjector
from app.graphs.contract_review.state import ContractReviewState, WORKFLOW_ID


class LegalContractReviewStateGraphRuntime:
    """Adapter that exposes the contract review StateGraph as AgentOS WorkflowRun objects."""

    def __init__(
        self,
        *,
        workflow_store: WorkflowStore,
        trace_store: TraceStore,
        checkpoint_store: CheckpointStore,
        review_manager: ReviewManager,
    ):
        self.workflow_store = workflow_store
        self.trace_store = trace_store
        self.checkpoint_store = checkpoint_store
        self.review_manager = review_manager
        self.graph = build_contract_review_graph()
        self.projector = ContractReviewRunProjector(
            workflow_store=workflow_store,
            trace_store=trace_store,
            checkpoint_store=checkpoint_store,
        )

    async def start(self, *, task: AgentTask, run: WorkflowRun, workflow: WorkflowDefinition) -> WorkflowRun:
        task.recommended_workflow = workflow.workflow_id
        task.status = WorkflowStatus.RUNNING
        task.updated_at = utc_now()
        self.workflow_store.save_task(task)

        self.trace_store.append(
            run=run,
            event_type=TraceEventType.TASK_CREATED,
            observation=f"Task created: {task.title}",
            payload=task.model_dump(by_alias=True, mode="json"),
        )
        self.trace_store.append(
            run=run,
            event_type=TraceEventType.RUN_STARTED,
            observation=f"LangGraph workflow started: {workflow.workflow_id}",
            payload={"workflowId": workflow.workflow_id, "threadId": run.run_id},
        )
        self.workflow_store.save_run(run)

        state = self._initial_state(run)
        result = self.graph.invoke(state, self._config(run.run_id))
        return self.projector.project(task=task, run=run, state=dict(result))

    async def apply_review(self, decision: ReviewDecision) -> WorkflowRun:
        run = self.workflow_store.get_run(decision.run_id)
        task = self.workflow_store.get_task(run.task_id)
        self.review_manager.record(run, decision)

        if decision.decision == ReviewDecisionType.APPROVED:
            review = {
                "status": ReviewDecisionType.APPROVED.value,
                "decision": ReviewDecisionType.APPROVED.value,
                "reviewer": decision.reviewer,
                "comment": decision.comment,
            }
            result = self.graph.invoke(
                Command(update={"review": review, "status": WorkflowStatus.RUNNING.value}),
                self._config(run.run_id),
            )
            return self.projector.project(task=task, run=run, state=dict(result))

        step = run.get_step("human_review")
        if decision.decision == ReviewDecisionType.NEED_MORE_INFO:
            step.status = StepStatus.WAITING_REVIEW
            run.status = WorkflowStatus.WAITING_REVIEW
            run.current_step_id = "human_review"
            run.error = decision.comment or "Human reviewer requested more information."
            run.updated_at = utc_now()
            task.status = WorkflowStatus.WAITING_REVIEW
            task.updated_at = utc_now()
            self.workflow_store.save_task(task)
            self.workflow_store.save_run(run)
            return run

        if decision.decision != ReviewDecisionType.REJECTED:
            raise ValueError(
                f"Unsupported review decision for {WORKFLOW_ID}: {decision.decision.value}"
            )

        step.status = StepStatus.FAILED
        run.status = WorkflowStatus.FAILED
        run.current_step_id = "human_review"
        run.error = decision.comment or "Human review rejected the workflow."
        run.updated_at = utc_now()
        task.status = WorkflowStatus.FAILED
        task.updated_at = utc_now()
        self.trace_store.append(
            run=run,
            event_type=TraceEventType.RUN_FAILED,
            step_id="human_review",
            observation=run.error,
        )
        self.workflow_store.save_task(task)
        self.workflow_store.save_run(run)
        return run

    def _initial_state(self, run: WorkflowRun) -> ContractReviewState:
        return {
            "run_id": run.run_id,
            "workflow_id": run.workflow_id,
            "contract_text": str(run.input.get("contractText") or run.input.get("contract_text") or ""),
            "current_step": "parse_contract",
            "status": WorkflowStatus.RUNNING.value,
            "steps": {
                step.step_id: {
                    "status": step.status.value,
                    "output": dict(step.output),
                }
                for step in run.steps
            },
            "risks": [],
            "evidences": [],
            "traces": [],
            "review": {},
            "artifacts": {},
            "report_markdown": "",
            "error": None,
        }

    @staticmethod
    def _config(run_id: str) -> Dict[str, Any]:
        return {"configurable": {"thread_id": run_id}}
