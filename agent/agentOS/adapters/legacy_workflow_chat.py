from __future__ import annotations

import os
from typing import Any, Awaitable, Callable, Dict, Optional, Type, TypeVar

from pydantic import BaseModel

from agentos.agents import AgentRegistry
from agentos.agents.base import AgentOutput, AgentProfile, AgentRunContext, BaseAgent
from agentos.core.types import (
    AgentTask,
    WorkflowDefinition,
    WorkflowRun,
    WorkflowStatus,
    WorkflowStep,
    WorkflowStepDefinition,
)
from agentos.core.workflow_registry import WorkflowRegistry
from agentos.core.workflow_runtime import WorkflowRuntime
from agentos.stores.memory_workflow_store import MemoryWorkflowStore

TRequest = TypeVar("TRequest", bound=BaseModel)
TResponse = TypeVar("TResponse", bound=BaseModel)


def compat_workflow_chat_enabled() -> bool:
    value = os.getenv("AGENTOS_COMPAT_WORKFLOW_CHAT", "").strip().lower()
    return value in {"1", "true", "yes", "on"}


class LegacyChatWorkflowAgent(BaseAgent):
    def __init__(
        self,
        *,
        role: str,
        request_model: Type[TRequest],
        legacy_runner: Callable[[TRequest], Awaitable[TResponse]],
        response_key: str = "legacyResponse",
    ):
        super().__init__(
            AgentProfile(
                agentName=f"{role}_legacy_chat_adapter",
                domain="legacy_chat",
                capabilities=[f"{role}_chat"],
                allowedSkills=[],
                description=f"Legacy workflow adapter for {role} chat",
            )
        )
        self.role = role
        self.request_model = request_model
        self.legacy_runner = legacy_runner
        self.response_key = response_key

    async def run(self, context: AgentRunContext) -> AgentOutput:
        request_payload = context.task.input.get("request", {})
        legacy_request = self.request_model.model_validate(request_payload)
        legacy_response = await self.legacy_runner(legacy_request)
        response_payload = legacy_response.model_dump(by_alias=True, mode="json")
        output = {
            "final_answer": response_payload.get("answer", ""),
            self.response_key: response_payload,
            "answer": response_payload.get("answer", ""),
            "skillsUsed": response_payload.get("skillsUsed", []),
            "trace": response_payload.get("trace", []),
            "federated": response_payload.get("federated", {}),
            "riskLevel": response_payload.get("riskLevel"),
            "workflowRunId": context.run.run_id,
            "workflowStatus": context.run.status.value,
            "workflowStepId": context.step.step_id,
        }
        for key, value in response_payload.items():
            output.setdefault(key, value)
        return AgentOutput(output=output, summary=response_payload.get("message", "legacy chat completed"))


async def run_legacy_chat_as_workflow(
    *,
    role: str,
    request: TRequest,
    request_model: Type[TRequest],
    response_model: Type[TResponse],
    legacy_runner: Callable[[TRequest], Awaitable[TResponse]],
) -> TResponse:
    agent_registry = AgentRegistry()
    workflow_registry = WorkflowRegistry()

    agent = LegacyChatWorkflowAgent(
        role=role,
        request_model=request_model,
        legacy_runner=legacy_runner,
    )
    agent_registry.register(agent)

    workflow = WorkflowDefinition(
        workflowId=f"{role}_legacy_chat_workflow",
        name=f"{role.title()} Legacy Chat Workflow",
        domain="legacy_chat",
        intent=f"{role}_chat",
        version="1.0.0",
        steps=[
            WorkflowStepDefinition(
                stepId="legacy_chat",
                name=f"{role.title()} Legacy Chat",
                agentName=agent.profile.agent_name,
            )
        ],
    )
    workflow_registry.register(workflow)

    runtime = WorkflowRuntime(
        agent_registry=agent_registry,
        workflow_registry=workflow_registry,
        workflow_store=MemoryWorkflowStore(),
    )
    task = runtime.create_task(
        title=f"{role.title()} legacy chat",
        domain="legacy_chat",
        intent=f"{role}_chat",
        input={"request": request.model_dump(by_alias=True, mode="json")},
    )
    run = await runtime.start(task.task_id, workflow_id=workflow.workflow_id)
    step_output = run.get_step("legacy_chat").output
    response_payload = dict(step_output.get("legacyResponse", {}))
    response_payload["workflowRunId"] = run.run_id
    response_payload["workflowStatus"] = run.status
    response_payload["workflowStepId"] = "legacy_chat"
    return response_model.model_validate(response_payload)
