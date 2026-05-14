from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.agent_core.orchestration.bootstrap import build_default_runtime
from app.agent_core.orchestration.types import ReviewDecision, ReviewDecisionType
from app.agent_core.orchestration.workflow_runtime import WorkflowRuntime


class AgentTaskCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    title: str
    domain: str = "general"
    intent: str = "general"
    input: Dict[str, Any] = Field(default_factory=dict)
    security_level: str = "internal"
    priority: str = "normal"

    @model_validator(mode="before")
    @classmethod
    def accept_camel_case(cls, data):
        if isinstance(data, dict) and "securityLevel" in data and "security_level" not in data:
            data = dict(data)
            data["security_level"] = data["securityLevel"]
        return data


class WorkflowRunCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    task_id: str
    workflow_id: Optional[str] = None
    review_mode: str = "auto"

    @model_validator(mode="before")
    @classmethod
    def accept_camel_case(cls, data):
        if isinstance(data, dict):
            data = dict(data)
            if "taskId" in data and "task_id" not in data:
                data["task_id"] = data["taskId"]
            if "workflowId" in data and "workflow_id" not in data:
                data["workflow_id"] = data["workflowId"]
            if "reviewMode" in data and "review_mode" not in data:
                data["review_mode"] = data["reviewMode"]
        return data


class ReviewDecisionRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    step_id: str
    decision: ReviewDecisionType
    reviewer: str = "system"
    comment: str = ""

    @model_validator(mode="before")
    @classmethod
    def accept_camel_case(cls, data):
        if isinstance(data, dict) and "stepId" in data and "step_id" not in data:
            data = dict(data)
            data["step_id"] = data["stepId"]
        return data


class ResumeRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    checkpoint_id: str

    @model_validator(mode="before")
    @classmethod
    def accept_camel_case(cls, data):
        if isinstance(data, dict) and "checkpointId" in data and "checkpoint_id" not in data:
            data = dict(data)
            data["checkpoint_id"] = data["checkpointId"]
        return data


def _to_json(model) -> Dict[str, Any]:
    return model.model_dump(by_alias=True, mode="json")


def create_router(runtime: WorkflowRuntime) -> APIRouter:
    router = APIRouter()

    @router.post("/core/tasks")
    async def create_task(request: AgentTaskCreateRequest):
        try:
            task = runtime.create_task(
                title=request.title,
                domain=request.domain,
                intent=request.intent,
                input=request.input,
                security_level=request.security_level,
                priority=request.priority,
            )
            return _to_json(task)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/core/workflows/runs")
    async def start_workflow(request: WorkflowRunCreateRequest):
        try:
            run = await runtime.start(
                task_id=request.task_id,
                workflow_id=request.workflow_id,
                review_mode=request.review_mode,
            )
            return _to_json(run)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/core/workflows/runs/{run_id}")
    async def get_workflow_run(run_id: str):
        try:
            return _to_json(runtime.get_status(run_id))
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("/core/workflows/runs/{run_id}/reviews")
    async def apply_review(run_id: str, request: ReviewDecisionRequest):
        try:
            run = await runtime.apply_review(
                ReviewDecision(
                    runId=run_id,
                    stepId=request.step_id,
                    decision=request.decision,
                    reviewer=request.reviewer,
                    comment=request.comment,
                )
            )
            return _to_json(run)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/core/workflows/runs/{run_id}/resume")
    async def resume_workflow(run_id: str, request: ResumeRequest):
        try:
            run = await runtime.resume_from_checkpoint(run_id=run_id, checkpoint_id=request.checkpoint_id)
            return _to_json(run)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/core/workflows/runs/{run_id}/cancel")
    async def cancel_workflow(run_id: str):
        try:
            return _to_json(runtime.cancel(run_id))
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    return router


runtime = build_default_runtime()
router = create_router(runtime)
