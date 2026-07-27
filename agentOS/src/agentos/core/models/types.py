"""AgentOS Core 的 types 模块，提供运行时控制、状态、Trace、审核或治理能力。"""


from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from agentos.core.models.enums import StepStatus, WorkflowProgressPhase
from agentos.core.runtime_graph import RuntimeGraph


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


class CoreModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    PLANNING = "planning"
    RUNNING = "running"
    WAITING_REVIEW = "waiting_review"
    RETRYING = "retrying"
    FAILED = "failed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class WorkflowDefinitionType(str, Enum):
    """Controls whether a definition is an executable template or a planner bootstrap."""

    TEMPLATE = "template"
    NATIVE_BOOTSTRAP = "native_bootstrap"


class TraceEventType(str, Enum):
    TASK_CREATED = "task_created"
    TASK_STATUS_CHANGED = "task_status_changed"
    TASK_ERROR = "task_error"
    RUN_STARTED = "run_started"
    STEP_SCHEDULED = "step_scheduled"
    STEP_STARTED = "step_started"
    AGENT_CALLED = "agent_called"
    STEP_SUCCEEDED = "step_succeeded"
    TOOL_CALLED = "tool_called"
    DATA_PRODUCED = "data_produced"
    DATA_CONSUMED = "data_consumed"
    CONTRACT_VIOLATION = "contract_violation"
    CHECKPOINT_CREATED = "checkpoint_created"
    RUNTIME_PATCH_APPLIED = "runtime_patch_applied"
    GRAPH_PATCH_APPLIED = "graph_patch_applied"
    RUNTIME_EVENT_CLASSIFIED = "runtime_event_classified"
    RUNTIME_EVENT_IGNORED = "runtime_event_ignored"
    GRAPH_CHANGE_PROPOSED = "graph_change_proposed"
    GRAPH_PATCH_REJECTED = "graph_patch_rejected"
    GRAPH_VERSION_CONFLICT = "graph_version_conflict"
    RUNTIME_RECIPE_SELECTED = "runtime_recipe_selected"
    RUNTIME_RECIPE_REAPPLICATION_BLOCKED = "runtime_recipe_reapplication_blocked"
    REVIEW_REQUIRED = "review_required"
    REVIEW_DECIDED = "review_decided"
    STEP_FAILED = "step_failed"
    RUN_FAILED = "run_failed"
    RUN_RECOVERED = "run_recovered"
    RUN_COMPLETED = "run_completed"
    RUN_CANCELLED = "run_cancelled"


class ReviewDecisionType(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    NEED_MORE_INFO = "need_more_info"
    RERUN = "rerun"
    CANCELLED = "cancelled"


class AgentTask(CoreModel):
    task_id: str = Field(default_factory=lambda: new_id("task"), alias="taskId")
    title: str
    domain: str = "general"
    intent: str = "general"
    input: Dict[str, Any] = Field(default_factory=dict)
    security_level: str = Field(default="internal", alias="securityLevel")
    priority: str = "normal"
    status: WorkflowStatus = WorkflowStatus.PENDING
    recommended_workflow: Optional[str] = Field(default=None, alias="recommendedWorkflow")
    created_at: datetime = Field(default_factory=utc_now, alias="createdAt")
    updated_at: datetime = Field(default_factory=utc_now, alias="updatedAt")


class WorkflowStepDefinition(CoreModel):
    step_id: str = Field(alias="stepId")
    name: str
    agent_name: str = Field(alias="agentName")
    capability: Optional[str] = None
    input: Dict[str, Any] = Field(default_factory=dict)
    output_spec: Dict[str, Any] = Field(default_factory=dict, alias="outputSpec")
    review_required: bool = Field(default=False, alias="reviewRequired")
    next_step_id: Optional[str] = Field(default=None, alias="nextStepId")
    max_retries: int = Field(default=0, alias="maxRetries")
    timeout: int = 0
    priority: int = 0


class WorkflowDefinition(CoreModel):
    workflow_id: str = Field(alias="workflowId")
    id: Optional[str] = None
    name: str
    domain: str
    intent: str = "general"
    version: str = "1.0.0"
    description: str = ""
    tags: List[str] = Field(default_factory=list)
    runtime_engine: str = Field(alias="runtimeEngine")
    definition_type: WorkflowDefinitionType = Field(
        default=WorkflowDefinitionType.TEMPLATE,
        alias="definitionType",
    )
    executor_type: Optional[str] = Field(default=None, alias="executorType")
    implementation_id: Optional[str] = Field(default=None, alias="implementationId")
    aliases: List[str] = Field(default_factory=list)
    artifacts: Dict[str, str] = Field(default_factory=dict)
    steps: List[WorkflowStepDefinition] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def normalize_identifier_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "workflowId" not in data and "workflow_id" not in data and "id" in data:
                data["workflowId"] = data["id"]
            if "id" not in data and ("workflowId" in data or "workflow_id" in data):
                data["id"] = data.get("workflowId") or data.get("workflow_id")
        return data

    @property
    def effective_runtime_engine(self) -> str:
        return self.runtime_engine.strip().lower()

    @property
    def effective_implementation_id(self) -> str:
        return (self.implementation_id or self.workflow_id).strip()

    @property
    def is_native_bootstrap(self) -> bool:
        return (
            self.effective_runtime_engine == "acg"
            and self.definition_type == WorkflowDefinitionType.NATIVE_BOOTSTRAP
        )

    def first_step_id(self) -> Optional[str]:
        return self.steps[0].step_id if self.steps else None

    def get_step_definition(self, step_id: str) -> WorkflowStepDefinition:
        for step in self.steps:
            if step.step_id == step_id:
                return step
        raise KeyError(f"workflow step not found: {step_id}")

class WorkflowStep(CoreModel):
    step_id: str = Field(alias="stepId")
    name: str
    agent_name: str = Field(alias="agentName")
    capability: Optional[str] = None
    status: StepStatus = StepStatus.PENDING
    input: Dict[str, Any] = Field(default_factory=dict)
    output_spec: Dict[str, Any] = Field(default_factory=dict, alias="outputSpec")
    resolved_input: Dict[str, Any] = Field(default_factory=dict, alias="resolvedInput")
    output: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    retry_count: int = Field(default=0, alias="retryCount")
    attempt: int = 0
    max_retries: int = Field(default=0, alias="maxRetries")
    timeout: int = 0
    priority: int = 0
    requires_review: bool = Field(default=False, alias="reviewRequired")
    started_at: Optional[datetime] = Field(default=None, alias="startedAt")
    completed_at: Optional[datetime] = Field(default=None, alias="completedAt")

    @classmethod
    def from_definition(cls, definition: WorkflowStepDefinition) -> "WorkflowStep":
        return cls(
            stepId=definition.step_id,
            name=definition.name,
            agentName=definition.agent_name,
            capability=definition.capability,
            input=dict(definition.input),
            outputSpec=dict(definition.output_spec),
            reviewRequired=definition.review_required,
            maxRetries=definition.max_retries,
            timeout=definition.timeout,
            priority=definition.priority,
        )


class TraceEvent(CoreModel):
    event_id: str = Field(default_factory=lambda: new_id("trace"), alias="eventId")
    run_id: Optional[str] = Field(default=None, alias="runId")
    step_id: Optional[str] = Field(default=None, alias="stepId")
    agent_name: Optional[str] = Field(default=None, alias="agentName")
    event_type: TraceEventType = Field(alias="eventType")
    observation: str = ""
    payload: Dict[str, Any] = Field(default_factory=dict)
    duration_ms: int = Field(default=0, alias="durationMs")
    created_at: datetime = Field(default_factory=utc_now, alias="createdAt")


class Checkpoint(CoreModel):
    checkpoint_id: str = Field(default_factory=lambda: new_id("ckpt"), alias="checkpointId")
    run_id: str = Field(alias="runId")
    step_id: str = Field(alias="stepId")
    state_snapshot: Dict[str, Any] = Field(default_factory=dict, alias="stateSnapshot")
    output_snapshot: Dict[str, Any] = Field(default_factory=dict, alias="outputSnapshot")
    can_resume: bool = Field(default=True, alias="canResume")
    created_at: datetime = Field(default_factory=utc_now, alias="createdAt")


class WorkflowRun(CoreModel):
    run_id: str = Field(default_factory=lambda: new_id("run"), alias="runId")
    task_id: str = Field(alias="taskId")
    workflow_id: str = Field(alias="workflowId")
    domain: str
    runtime_engine: str = Field(alias="runtimeEngine")
    implementation_id: Optional[str] = Field(default=None, alias="implementationId")
    status: WorkflowStatus = WorkflowStatus.PENDING
    lifecycle_phase: Optional[WorkflowProgressPhase] = Field(default=None, alias="lifecyclePhase")
    lifecycle_message: Optional[str] = Field(default=None, alias="lifecycleMessage")
    started_at: Optional[datetime] = Field(default=None, alias="startedAt")
    idempotency_key: Optional[str] = Field(default=None, alias="idempotencyKey")
    idempotency_fingerprint: Optional[str] = Field(default=None, alias="idempotencyFingerprint")
    current_step_id: Optional[str] = Field(default=None, alias="currentStepId")
    review_mode: str = Field(default="auto", alias="reviewMode")
    input: Dict[str, Any] = Field(default_factory=dict)
    output: Dict[str, Any] = Field(default_factory=dict)
    steps: List[WorkflowStep] = Field(default_factory=list)
    checkpoints: List[Checkpoint] = Field(default_factory=list)
    trace: List[TraceEvent] = Field(default_factory=list)
    error: Optional[str | Dict[str, Any]] = None
    recovery_count: int = Field(default=0, alias="recoveryCount")
    # ACG 执行路径承载字段（可选，仅 runtimeEngine=acg 时填充）。
    # acg_blueprint 存规划器产物 / 升格结果；completed_step_ids 记录就绪集调度
    # 已完成的 StepNode，用于并行调度时计算下一批就绪集，不影响线性路径。
    acg_blueprint: Optional[Dict[str, Any]] = Field(default=None, alias="acgBlueprint")
    # Stage one: authoritative runtime structure/version/patch history.  WorkflowStep
    # remains the execution-state authority until the executor is migrated.
    runtime_graph: Optional[RuntimeGraph] = Field(default=None, alias="runtimeGraph")
    completed_step_ids: List[str] = Field(default_factory=list, alias="completedStepIds")
    active_step_ids: List[str] = Field(default_factory=list, alias="activeStepIds")
    # 数据血缘图（低熵通信审计产物，ACG 路径填充）：生产/消费事件，供前端血缘面板。
    provenance: Optional[Dict[str, Any]] = Field(default=None)
    execution_state: Dict[str, Any] = Field(default_factory=dict, alias="executionState")
    created_at: datetime = Field(default_factory=utc_now, alias="createdAt")
    updated_at: datetime = Field(default_factory=utc_now, alias="updatedAt")

    def get_step(self, step_id: str) -> WorkflowStep:
        for step in self.steps:
            if step.step_id == step_id:
                return step
        raise KeyError(f"workflow run step not found: {step_id}")


class ReviewDecision(CoreModel):
    run_id: str = Field(alias="runId")
    step_id: str = Field(alias="stepId")
    decision: ReviewDecisionType
    reviewer: str = "system"
    comment: str = ""
    operation_id: Optional[str] = Field(default=None, alias="operationId")
    expected_run_updated_at: Optional[datetime] = Field(default=None, alias="expectedRunUpdatedAt")
    expected_step_status: Optional[StepStatus] = Field(default=None, alias="expectedStepStatus")
    created_at: datetime = Field(default_factory=utc_now, alias="createdAt")


class ReviewRecord(CoreModel):
    review_id: str = Field(default_factory=lambda: new_id("review"), alias="reviewId")
    run_id: str = Field(alias="runId")
    step_id: str = Field(alias="stepId")
    decision: ReviewDecisionType
    reviewer: str = "system"
    comment: str = ""
    operation_id: Optional[str] = Field(default=None, alias="operationId")
    trace_event_id: Optional[str] = Field(default=None, alias="traceEventId")
    created_at: datetime = Field(default_factory=utc_now, alias="createdAt")


class WorkflowMetric(CoreModel):
    total_runs: int = Field(default=0, alias="totalRuns")
    completed_runs: int = Field(default=0, alias="completedRuns")
    failed_runs: int = Field(default=0, alias="failedRuns")
    cancelled_runs: int = Field(default=0, alias="cancelledRuns")
    waiting_review_runs: int = Field(default=0, alias="waitingReviewRuns")
    retrying_runs: int = Field(default=0, alias="retryingRuns")
    completion_rate: float = Field(default=0.0, alias="completionRate")
    failure_rate: float = Field(default=0.0, alias="failureRate")
    recovery_success_rate: float = Field(default=0.0, alias="recoverySuccessRate")
    average_recovery_count: float = Field(default=0.0, alias="averageRecoveryCount")
    average_trace_events: float = Field(default=0.0, alias="averageTraceEvents")
    review_count: int = Field(default=0, alias="reviewCount")
    status_breakdown: Dict[str, int] = Field(default_factory=dict, alias="statusBreakdown")


class EvaluationRun(CoreModel):
    evaluation_id: str = Field(default_factory=lambda: new_id("eval"), alias="evaluationId")
    domain: Optional[str] = None
    workflow_id: Optional[str] = Field(default=None, alias="workflowId")
    source: Optional[str] = None
    metrics: WorkflowMetric
    created_at: datetime = Field(default_factory=utc_now, alias="createdAt")


class SkillRequest(CoreModel):
    session_id: str = Field(alias="sessionId")
    text: str
    action_input: Dict[str, Any] = Field(default_factory=dict, alias="actionInput")
    memory: Dict[str, Any] = Field(default_factory=dict)


class SkillResult(CoreModel):
    skill_name: str = Field(alias="skillName")
    success: bool = True
    output: Dict[str, Any] = Field(default_factory=dict)
    message: str = ""
