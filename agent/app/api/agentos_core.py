from typing import Any, Dict, Literal, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, ConfigDict, Field, model_validator

from agentos.core.types import ReviewDecision, ReviewDecisionType
from agentos.core.workflow_runtime import WorkflowRuntime, build_default_runtime


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


class WorkflowStartRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    title: str
    domain: str = "general"
    intent: str = "general"
    input: Dict[str, Any] = Field(default_factory=dict)
    security_level: str = "internal"
    priority: str = "normal"
    workflow_id: Optional[str] = None
    review_mode: str = "auto"

    @model_validator(mode="before")
    @classmethod
    def accept_camel_case(cls, data):
        if isinstance(data, dict):
            data = dict(data)
            if "securityLevel" in data and "security_level" not in data:
                data["security_level"] = data["securityLevel"]
            if "workflowId" in data and "workflow_id" not in data:
                data["workflow_id"] = data["workflowId"]
            if "reviewMode" in data and "review_mode" not in data:
                data["review_mode"] = data["reviewMode"]
        return data


class ChatWorkflowUpgradeRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    text: str = Field(..., min_length=1)
    title: Optional[str] = None
    domain: str = "legal"
    intent: str = "case_analysis"
    workflow_id: Optional[str] = None
    review_mode: str = "human_in_loop"
    role_id: Optional[str] = None
    context_id: Optional[str] = None
    context: Optional[list[Dict[str, Any]]] = None
    input: Dict[str, Any] = Field(default_factory=dict)
    security_level: str = "internal"
    priority: str = "normal"

    @model_validator(mode="before")
    @classmethod
    def accept_camel_case(cls, data):
        if isinstance(data, dict):
            data = dict(data)
            if "workflowId" in data and "workflow_id" not in data:
                data["workflow_id"] = data["workflowId"]
            if "reviewMode" in data and "review_mode" not in data:
                data["review_mode"] = data["reviewMode"]
            if "roleId" in data and "role_id" not in data:
                data["role_id"] = data["roleId"]
            if "contextId" in data and "context_id" not in data:
                data["context_id"] = data["contextId"]
            if "securityLevel" in data and "security_level" not in data:
                data["security_level"] = data["securityLevel"]
        return data


class ReviewRequest(BaseModel):
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


def _page_to_json(page) -> Dict[str, Any]:
    return {
        "items": [_to_json(item) for item in page.items],
        "total": page.total,
        "page": page.page,
        "pageSize": page.page_size,
    }


async def _create_task_and_start(
    runtime: WorkflowRuntime,
    request: WorkflowStartRequest,
) -> Dict[str, Any]:
    task = runtime.create_task(
        title=request.title,
        domain=request.domain,
        intent=request.intent,
        input=request.input,
        security_level=request.security_level,
        priority=request.priority,
    )
    run = await runtime.start(
        task_id=task.task_id,
        workflow_id=request.workflow_id,
        review_mode=request.review_mode,
    )
    return {"task": _to_json(task), "run": _to_json(run)}


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

    @router.get("/core/tasks")
    async def list_tasks(
        status: Optional[str] = None,
        domain: Optional[str] = None,
        source: Optional[str] = None,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, alias="pageSize"),
    ):
        return _page_to_json(
            runtime.workflow_store.list_tasks(
                status=status,
                domain=domain,
                source=source,
                page=page,
                page_size=page_size,
            )
        )

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

    @router.post("/core/workflows/start")
    async def start_workflow_from_workbench(request: WorkflowStartRequest):
        try:
            return await _create_task_and_start(runtime, request)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/chat/workflows/upgrade")
    async def upgrade_chat_to_workflow(request: ChatWorkflowUpgradeRequest):
        text = request.text.strip()
        workflow_input = {
            **request.input,
            "source": "chat",
            "caseText": request.input.get("caseText") or text,
            "chatText": text,
        }
        if request.context_id:
            workflow_input["chatContextId"] = request.context_id
        if request.role_id:
            workflow_input["chatRoleId"] = request.role_id
        if request.context:
            workflow_input["chatContext"] = request.context

        title = request.title or f"Chat升级工作流：{text[:30]}"
        start_request = WorkflowStartRequest(
            title=title,
            domain=request.domain,
            intent=request.intent,
            input=workflow_input,
            securityLevel=request.security_level,
            priority=request.priority,
            workflowId=request.workflow_id,
            reviewMode=request.review_mode,
        )
        try:
            payload = await _create_task_and_start(runtime, start_request)
            payload["source"] = "chat"
            return payload
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/core/workflows/runs")
    async def list_workflow_runs(
        status: Optional[str] = None,
        domain: Optional[str] = None,
        workflow_id: Optional[str] = Query(None, alias="workflowId"),
        source: Optional[str] = None,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, alias="pageSize"),
    ):
        return _page_to_json(
            runtime.workflow_store.list_runs(
                status=status,
                domain=domain,
                workflow_id=workflow_id,
                source=source,
                page=page,
                page_size=page_size,
            )
        )

    @router.get("/core/workflows/metrics")
    async def evaluate_workflows(
        status: Optional[str] = None,
        domain: Optional[str] = None,
        workflow_id: Optional[str] = Query(None, alias="workflowId"),
        source: Optional[str] = None,
    ):
        return _to_json(
            runtime.evaluate_runs(
                status=status,
                domain=domain,
                workflow_id=workflow_id,
                source=source,
            )
        )

    @router.get("/core/workflows/runs/{run_id}")
    async def get_workflow_run(run_id: str):
        try:
            return _to_json(runtime.get_status(run_id))
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get("/core/workflows/runs/{run_id}/checkpoints")
    async def list_checkpoints(run_id: str):
        try:
            checkpoints = runtime.list_checkpoints(run_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {
            "items": [_to_json(checkpoint) for checkpoint in checkpoints],
            "total": len(checkpoints),
            "runId": run_id,
        }

    @router.get("/core/workflows/runs/{run_id}/trace")
    async def export_workflow_trace(
        run_id: str,
        format: Literal["json", "markdown"] = "json",
    ):
        try:
            run = runtime.get_status(run_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

        if format == "markdown":
            return PlainTextResponse(
                runtime.trace_store.export_markdown(run),
                media_type="text/markdown; charset=utf-8",
            )
        return runtime.trace_store.export_json(run)

    @router.get("/core/workflows/runs/{run_id}/reviews")
    async def list_reviews(run_id: str):
        try:
            reviews = runtime.list_reviews(run_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {
            "items": [_to_json(review) for review in reviews],
            "total": len(reviews),
            "runId": run_id,
        }

    @router.post("/core/workflows/runs/{run_id}/reviews")
    async def apply_review(run_id: str, request: ReviewRequest):
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
