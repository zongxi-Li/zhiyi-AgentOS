import asyncio

from agentos.agents import AgentRegistry
from agentos.core.models.types import ReviewDecision, ReviewDecisionType, WorkflowStatus
from agentos.core.runtime import WorkflowRuntime
from agentos.core.workflow.registry import WorkflowRegistry
from app.execution.runtime import configure_execution_adapters
from packs.legal import register_pack as register_legal_pack


def _runtime() -> WorkflowRuntime:
    agent_registry = AgentRegistry()
    workflow_registry = WorkflowRegistry()
    register_legal_pack(agent_registry=agent_registry, workflow_registry=workflow_registry)
    return configure_execution_adapters(
        WorkflowRuntime(agent_registry=agent_registry, workflow_registry=workflow_registry)
    )


def test_langgraph_contract_review_legacy_id_is_alias_to_canonical_workflow():
    asyncio.run(_test_langgraph_contract_review_legacy_id_is_alias_to_canonical_workflow())


async def _test_langgraph_contract_review_legacy_id_is_alias_to_canonical_workflow():
    runtime = _runtime()
    workflow = runtime.workflow_registry.get("legal_contract_review_langgraph_v1")

    assert workflow.workflow_id == "legal_contract_review_v1"
    assert workflow.runtime_engine == "langgraph"
    assert workflow.implementation_id == "legal_contract_review_stategraph_v1"
    assert "legal_contract_review_langgraph_v1" in workflow.aliases

    task = runtime.create_task(
        title="软件开发服务合同审查",
        domain="legal",
        intent="contract_review_langgraph",
        input={
            "source": "workbench",
            "contractText": "甲方委托乙方开发 CRM 系统，合同约定签署后支付 30%，系统上线后支付 70%。",
        },
        workflow_id="legal_contract_review_langgraph_v1",
    )

    run = await runtime.start(
        task_id=task.task_id,
        workflow_id="legal_contract_review_langgraph_v1",
        review_mode="human_in_loop",
    )

    assert run.workflow_id == "legal_contract_review_v1"
    assert run.runtime_engine == "langgraph"
    assert run.implementation_id == "legal_contract_review_stategraph_v1"
    assert run.status == WorkflowStatus.WAITING_REVIEW
    assert run.current_step_id == "human_review"
    assert "report_generate" not in run.output["artifacts"]

    completed = await runtime.apply_review(
        ReviewDecision(
            runId=run.run_id,
            stepId="human_review",
            decision=ReviewDecisionType.APPROVED,
            reviewer="legal_reviewer",
            comment="风险结论可进入报告生成。",
        )
    )

    assert completed.status == WorkflowStatus.COMPLETED
    assert completed.output["artifacts"]["report_generate"]["report_markdown"]
