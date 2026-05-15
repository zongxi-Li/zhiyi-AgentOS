import asyncio

import pytest

from core.agents.base import AgentOutput, AgentProfile, BaseAgent
from core.agents.registry import AgentRegistry
from core.packs.legal import register_pack as register_legal_pack
from core.state_machine import InvalidStateTransition, StateMachine
from core.types import (
    ReviewDecision,
    ReviewDecisionType,
    StepStatus,
    TraceEventType,
    WorkflowDefinition,
    WorkflowStatus,
    WorkflowStepDefinition,
)
from core.workflow_registry import WorkflowRegistry
from core.workflow_runtime import WorkflowRuntime


class RecordingAgent(BaseAgent):
    def __init__(self, name, calls, fail_once=False):
        super().__init__(
            AgentProfile(
                agentName=name,
                domain="test",
                capabilities=[name],
                allowedSkills=[],
            )
        )
        self.calls = calls
        self.fail_once = fail_once
        self.failed = False

    async def run(self, context):
        self.calls.append(
            {
                "agent": self.profile.agent_name,
                "step": context.step.step_id,
                "observations": sorted(context.memory.observations.keys()),
            }
        )
        if self.fail_once and not self.failed:
            self.failed = True
            raise RuntimeError("planned failure")
        return AgentOutput(
            output={
                "agent": self.profile.agent_name,
                "step": context.step.step_id,
                "observations": dict(context.memory.observations),
            },
            summary=f"{self.profile.agent_name} completed",
        )


def _runtime_with_workflow(steps, agents):
    agent_registry = AgentRegistry()
    for agent in agents:
        agent_registry.register(agent)

    workflow_registry = WorkflowRegistry()
    workflow_registry.register(
        WorkflowDefinition(
            workflowId="test_workflow",
            name="Test Workflow",
            domain="test",
            intent="case_analysis",
            version="1.0.0",
            steps=steps,
        )
    )
    return WorkflowRuntime(
        agent_registry=agent_registry,
        workflow_registry=workflow_registry,
    )


def test_state_machine_blocks_illegal_transitions():
    machine = StateMachine()

    assert machine.transition(WorkflowStatus.PENDING, WorkflowStatus.RUNNING) == WorkflowStatus.RUNNING

    with pytest.raises(InvalidStateTransition):
        machine.transition(WorkflowStatus.COMPLETED, WorkflowStatus.RUNNING)


def test_runtime_runs_registered_workflow_with_trace_and_checkpoints():
    asyncio.run(_test_runtime_runs_registered_workflow_with_trace_and_checkpoints())


async def _test_runtime_runs_registered_workflow_with_trace_and_checkpoints():
    calls = []
    steps = [
        WorkflowStepDefinition(stepId="intake", name="Intake", agentName="intake", nextStepId="statute"),
        WorkflowStepDefinition(stepId="statute", name="Statute", agentName="statute", nextStepId="risk"),
        WorkflowStepDefinition(stepId="risk", name="Risk", agentName="risk"),
    ]
    runtime = _runtime_with_workflow(
        steps=steps,
        agents=[
            RecordingAgent("intake", calls),
            RecordingAgent("statute", calls),
            RecordingAgent("risk", calls),
        ],
    )

    task = runtime.create_task(
        title="Test case",
        domain="test",
        intent="case_analysis",
        input={"caseText": "合同违约并存在转账证据"},
    )
    run = await runtime.start(task.task_id, workflow_id="test_workflow")

    assert run.status == WorkflowStatus.COMPLETED
    assert [call["agent"] for call in calls] == ["intake", "statute", "risk"]
    assert calls[1]["observations"] == ["intake"]
    assert calls[2]["observations"] == ["intake", "statute"]
    assert all(step.status == StepStatus.COMPLETED for step in run.steps)
    assert len(run.checkpoints) == 3
    assert [checkpoint.step_id for checkpoint in run.checkpoints] == ["intake", "statute", "risk"]

    event_types = [event.event_type for event in run.trace]
    assert TraceEventType.TASK_CREATED in event_types
    assert TraceEventType.STEP_STARTED in event_types
    assert TraceEventType.AGENT_CALLED in event_types
    assert TraceEventType.CHECKPOINT_CREATED in event_types
    assert TraceEventType.RUN_COMPLETED in event_types


def test_runtime_waits_for_review_and_continues_after_approval():
    asyncio.run(_test_runtime_waits_for_review_and_continues_after_approval())


async def _test_runtime_waits_for_review_and_continues_after_approval():
    calls = []
    steps = [
        WorkflowStepDefinition(stepId="intake", name="Intake", agentName="intake", nextStepId="risk"),
        WorkflowStepDefinition(
            stepId="risk",
            name="Risk",
            agentName="risk",
            reviewRequired=True,
            nextStepId="draft",
        ),
        WorkflowStepDefinition(stepId="draft", name="Draft", agentName="draft"),
    ]
    runtime = _runtime_with_workflow(
        steps=steps,
        agents=[
            RecordingAgent("intake", calls),
            RecordingAgent("risk", calls),
            RecordingAgent("draft", calls),
        ],
    )
    task = runtime.create_task("Review task", "test", "case_analysis", {"caseText": "需要人工审核"})

    run = await runtime.start(task.task_id, workflow_id="test_workflow", review_mode="human_in_loop")

    assert run.status == WorkflowStatus.WAITING_REVIEW
    assert run.current_step_id == "risk"
    assert run.get_step("risk").status == StepStatus.WAITING_REVIEW
    assert [call["agent"] for call in calls] == ["intake", "risk"]

    reviewed = await runtime.apply_review(
        ReviewDecision(
            runId=run.run_id,
            stepId="risk",
            decision=ReviewDecisionType.APPROVED,
            reviewer="reviewer_001",
            comment="风险说明可进入文书生成",
        )
    )

    assert reviewed.status == WorkflowStatus.COMPLETED
    assert [call["agent"] for call in calls] == ["intake", "risk", "draft"]
    assert reviewed.get_step("draft").status == StepStatus.COMPLETED


def test_runtime_recovers_from_checkpoint_after_step_failure():
    asyncio.run(_test_runtime_recovers_from_checkpoint_after_step_failure())


async def _test_runtime_recovers_from_checkpoint_after_step_failure():
    calls = []
    steps = [
        WorkflowStepDefinition(stepId="intake", name="Intake", agentName="intake", nextStepId="risk"),
        WorkflowStepDefinition(stepId="risk", name="Risk", agentName="risk"),
    ]
    runtime = _runtime_with_workflow(
        steps=steps,
        agents=[
            RecordingAgent("intake", calls),
            RecordingAgent("risk", calls, fail_once=True),
        ],
    )
    task = runtime.create_task("Recover task", "test", "case_analysis", {"caseText": "第一次风险评估失败"})

    failed = await runtime.start(task.task_id, workflow_id="test_workflow")

    assert failed.status == WorkflowStatus.FAILED
    assert failed.current_step_id == "risk"
    assert failed.get_step("risk").status == StepStatus.FAILED
    assert [checkpoint.step_id for checkpoint in failed.checkpoints] == ["intake"]

    recovered = await runtime.resume_from_checkpoint(
        run_id=failed.run_id,
        checkpoint_id=failed.checkpoints[-1].checkpoint_id,
    )

    assert recovered.status == WorkflowStatus.COMPLETED
    assert recovered.recovery_count == 1
    assert recovered.get_step("risk").status == StepStatus.COMPLETED
    event_types = [event.event_type for event in recovered.trace]
    assert TraceEventType.RUN_RECOVERED in event_types


def test_legal_demo_pack_registers_agents_and_workflow():
    asyncio.run(_test_legal_demo_pack_registers_agents_and_workflow())


async def _test_legal_demo_pack_registers_agents_and_workflow():
    agent_registry = AgentRegistry()
    workflow_registry = WorkflowRegistry()
    register_legal_pack(agent_registry=agent_registry, workflow_registry=workflow_registry)
    runtime = WorkflowRuntime(agent_registry=agent_registry, workflow_registry=workflow_registry)

    task = runtime.create_task(
        title="合同审查",
        domain="legal",
        intent="contract_review",
        input={"caseText": "甲乙双方合同逾期交付，存在转账记录和微信聊天证据。"},
    )
    run = await runtime.start(task.task_id, review_mode="human_in_loop")

    assert task.recommended_workflow == "legal_contract_review_v1"
    assert run.status == WorkflowStatus.WAITING_REVIEW
    assert run.current_step_id == "risk"
    assert run.get_step("case_intake").output["case_summary"]
    assert run.get_step("statute").output["legal_basis"]

    completed = await runtime.apply_review(
        ReviewDecision(
            runId=run.run_id,
            stepId="risk",
            decision=ReviewDecisionType.APPROVED,
            reviewer="legal_reviewer",
        )
    )

    assert completed.status == WorkflowStatus.COMPLETED
    assert completed.output["final_answer"]
    assert completed.output["artifacts"]["draft"]


def test_agentos_core_api_task_run_review_flow():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.api.agentos_core import create_router

    agent_registry = AgentRegistry()
    workflow_registry = WorkflowRegistry()
    register_legal_pack(agent_registry=agent_registry, workflow_registry=workflow_registry)
    runtime = WorkflowRuntime(agent_registry=agent_registry, workflow_registry=workflow_registry)

    app = FastAPI()
    app.include_router(create_router(runtime), prefix="/ai")
    client = TestClient(app)

    task_response = client.post(
        "/ai/core/tasks",
        json={
            "title": "合同审查",
            "domain": "legal",
            "intent": "contract_review",
            "input": {"caseText": "合同逾期交付，存在转账记录。"},
            "securityLevel": "internal",
        },
    )
    assert task_response.status_code == 200
    task_payload = task_response.json()
    assert task_payload["recommendedWorkflow"] == "legal_contract_review_v1"

    run_response = client.post(
        "/ai/core/workflows/runs",
        json={"taskId": task_payload["taskId"], "reviewMode": "human_in_loop"},
    )
    assert run_response.status_code == 200
    run_payload = run_response.json()
    assert run_payload["status"] == "waiting_review"
    assert run_payload["currentStepId"] == "risk"

    review_response = client.post(
        f"/ai/core/workflows/runs/{run_payload['runId']}/reviews",
        json={"stepId": "risk", "decision": "approved", "reviewer": "api_reviewer"},
    )
    assert review_response.status_code == 200
    assert review_response.json()["status"] == "completed"

    status_response = client.get(f"/ai/core/workflows/runs/{run_payload['runId']}")
    assert status_response.status_code == 200
    assert status_response.json()["output"]["final_answer"]
