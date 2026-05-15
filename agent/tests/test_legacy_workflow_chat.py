from agentos.adapters.legacy_workflow_chat import run_legacy_chat_as_workflow
from agentos.core.types import AgentLawyerRequest, AgentLawyerResponse, WorkflowStatus


async def test_legacy_workflow_chat_wraps_response_in_workflow_run():
    async def fake_legacy_runner(request: AgentLawyerRequest) -> AgentLawyerResponse:
        return AgentLawyerResponse(
            success=True,
            answer=f"legacy:{request.text}",
            sessionId=request.session_id or "session_001",
            skillsUsed=["case_understanding"],
            trace=[],
            federated={},
            message="律师 Agent 工作流执行完成。",
        )

    request = AgentLawyerRequest(text="合同违约如何处理", sessionId="session_001")
    response = await run_legacy_chat_as_workflow(
        role="lawyer",
        request=request,
        request_model=AgentLawyerRequest,
        response_model=AgentLawyerResponse,
        legacy_runner=fake_legacy_runner,
    )

    assert response.answer == "legacy:合同违约如何处理"
    assert response.workflow_run_id
    assert response.workflow_status == WorkflowStatus.COMPLETED
    assert response.workflow_step_id == "legacy_chat"
    assert response.session_id == "session_001"


async def test_lawyer_route_uses_workflow_adapter_when_enabled(monkeypatch):
    from app.api import agent_lawyer

    async def fake_legacy_runner(request: AgentLawyerRequest) -> AgentLawyerResponse:
        return AgentLawyerResponse(
            success=True,
            answer=f"wrapped:{request.text}",
            sessionId=request.session_id or "session_002",
            skillsUsed=["case_understanding"],
            trace=[],
            federated={},
            message="律师 Agent 工作流执行完成。",
        )

    monkeypatch.setenv("AGENTOS_COMPAT_WORKFLOW_CHAT", "1")
    monkeypatch.setattr(agent_lawyer, "_lawyer_agent_chat_legacy", fake_legacy_runner)

    response = await agent_lawyer.lawyer_agent_chat(
        AgentLawyerRequest(text="合同违约如何处理", sessionId="session_002")
    )

    assert response.answer == "wrapped:合同违约如何处理"
    assert response.workflow_run_id
    assert response.workflow_status == WorkflowStatus.COMPLETED
    assert response.workflow_step_id == "legacy_chat"
