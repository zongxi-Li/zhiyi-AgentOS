from __future__ import annotations

import json

from agentos.agents import AgentRegistry
from agentos.core.models.types import WorkflowDefinition, WorkflowStepDefinition
from agentos.core.native import NATIVE_ACG_WORKFLOW_ID, register_native_runtime
from agentos.core.runtime import WorkflowRuntime
from agentos.core.workflow.registry import WorkflowRegistry


class RecordingIntentLLM:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def generate_json(self, prompt, schema, **kwargs):
        self.calls.append({"prompt": prompt, "schema": schema, "kwargs": kwargs})
        return {
            "data": {
                "primaryGoal": "形成可验证的分析报告",
                "requiredCapabilities": [
                    "task_understanding",
                    "analysis",
                    "artifact_generation",
                ],
                "estimatedComplexity": "medium",
                "domainHint": "general",
                "taskTypeHint": "general",
            },
            "metadata": {"provider": "test", "model": "intent-test"},
        }


def _template(workflow_id: str) -> WorkflowDefinition:
    return WorkflowDefinition(
        workflowId=workflow_id,
        name="通用分析报告模板",
        domain="general",
        intent="general",
        runtimeEngine="acg",
        description=(
            "形成可验证的分析报告 task_understanding analysis artifact_generation"
        ),
        tags=["task_understanding", "analysis", "artifact_generation"],
        steps=[
            WorkflowStepDefinition(
                stepId="understand",
                name="理解任务",
                agentName="native_general_agent",
                capability="task_understanding",
            ),
            WorkflowStepDefinition(
                stepId="analyze",
                name="分析",
                agentName="native_general_agent",
                capability="analysis",
            ),
            WorkflowStepDefinition(
                stepId="deliver",
                name="交付",
                agentName="native_general_agent",
                capability="artifact_generation",
            ),
        ],
    )


def _runtime(*, with_template: bool = False) -> WorkflowRuntime:
    agents = AgentRegistry()
    workflows = WorkflowRegistry()
    register_native_runtime(agent_registry=agents, workflow_registry=workflows)
    if with_template:
        workflows.register(_template("general_report_template"))
    return WorkflowRuntime(agent_registry=agents, workflow_registry=workflows)


def _plan(runtime: WorkflowRuntime, task_id: str):
    task, run = runtime.prepare_run(task_id)
    workflow = runtime._workflow_for_run(run)
    blueprint = runtime._build_acg_blueprint(task, run, workflow)
    return run, blueprint


def test_native_bootstrap_template_preferred_calls_llm_and_reuses_template():
    runtime = _runtime(with_template=True)
    llm = RecordingIntentLLM()
    runtime.set_intent_llm(llm)
    task = runtime.create_task(
        title="生成分析报告",
        input={
            "taskGoal": "形成可验证的分析报告",
            "usePlanner": True,
            "planningMode": "template_preferred",
        },
    )

    run, blueprint = _plan(runtime, task.task_id)

    assert run.workflow_id == NATIVE_ACG_WORKFLOW_ID
    assert len(llm.calls) == 1
    diagnostics = run.execution_state["planningDiagnostics"]
    assert diagnostics["intentParseSource"] == "llm"
    assert diagnostics["effectiveStrategy"] == "static_template"
    assert diagnostics["templateId"] == "general_report_template"
    assert blueprint.metadata["planningDiagnostics"] == diagnostics


def test_dynamic_mode_skips_matching_template_but_still_calls_llm():
    runtime = _runtime(with_template=True)
    llm = RecordingIntentLLM()
    runtime.set_intent_llm(llm)
    task = runtime.create_task(
        title="生成分析报告",
        input={
            "taskGoal": "形成可验证的分析报告",
            "usePlanner": True,
            "planningMode": "dynamic",
        },
    )

    run, _ = _plan(runtime, task.task_id)

    assert len(llm.calls) == 1
    diagnostics = run.execution_state["planningDiagnostics"]
    assert diagnostics["intentParseSource"] == "llm"
    assert diagnostics["effectiveStrategy"] == "dynamic_generation"
    assert diagnostics["templateId"] is None


def test_explicit_workflow_wins_over_dynamic_and_legacy_force_flag():
    runtime = _runtime(with_template=True)
    task = runtime.create_task(
        title="显式模板任务",
        workflow_id="general_report_template",
        input={
            "taskGoal": "形成可验证的分析报告",
            "usePlanner": True,
            "planningMode": "dynamic",
            "forceDynamicPlanning": True,
        },
    )

    run, _ = _plan(runtime, task.task_id)

    assert run.workflow_id == "general_report_template"
    assert run.workflow_selection_source == "explicit"
    diagnostics = run.execution_state["planningDiagnostics"]
    assert diagnostics["effectiveStrategy"] == "static_template"
    assert diagnostics["templateId"] == "general_report_template"


def test_legacy_force_flag_only_applies_when_planning_mode_is_absent():
    runtime = _runtime(with_template=True)
    llm = RecordingIntentLLM()
    runtime.set_intent_llm(llm)
    task = runtime.create_task(
        title="模式优先级",
        input={
            "taskGoal": "形成可验证的分析报告",
            "usePlanner": True,
            "planningMode": "unsupported-client-value",
            "forceDynamicPlanning": True,
        },
    )

    run, _ = _plan(runtime, task.task_id)

    diagnostics = run.execution_state["planningDiagnostics"]
    assert diagnostics["requestedPlanningMode"] == "template_preferred"
    assert diagnostics["effectiveStrategy"] == "static_template"


def test_material_requirements_change_dynamic_capability_topology():
    runtime = _runtime()
    task = runtime.create_task(
        title="审阅附件",
        input={
            "taskGoal": "审阅附件并完成任务",
            "usePlanner": True,
            "planningMode": "dynamic",
            "materialText": (
                "附件要求梳理系统架构和数据流，执行资料检索，识别安全风险，"
                "执行结论验证，并形成最终报告。 PRIVATE_RUNTIME_MATERIAL"
            ),
        },
    )

    run, blueprint = _plan(runtime, task.task_id)

    capabilities = {step.capability for step in blueprint.step_nodes()}
    assert {
        "architecture_design",
        "information_retrieval",
        "risk_analysis",
        "verification",
        "artifact_generation",
    }.issubset(capabilities)
    diagnostics = run.execution_state["planningDiagnostics"]
    assert diagnostics["intentParseSource"] == "heuristic"
    assert diagnostics["intentFallbackReason"] == "llm_unavailable"
    assert diagnostics["materialContext"]["totalCharacters"] > 0
    persisted = json.dumps(
        {
            "executionState": run.execution_state,
            "trace": [event.payload for event in run.trace],
            "blueprintMetadata": blueprint.metadata,
        },
        ensure_ascii=False,
    )
    assert "PRIVATE_RUNTIME_MATERIAL" not in persisted


def test_acceptance_tasks_produce_at_least_three_distinct_capability_topologies():
    tasks = [
        "并购尽调：执行资料检索、证据分析和风险分析，形成最终报告。",
        "灾备演练：设计系统架构，拆解流程并规划资源，完成风险分析、验证和报告。",
        "供应商比较：检索供应商资料，开展方案比较、成本分析和风险分析，输出报告。",
        "附件审阅：抽取附件要素，完成证据分析和结论验证，生成审阅报告。",
    ]
    topologies: list[frozenset[str]] = []

    for index, intent in enumerate(tasks):
        runtime = _runtime()
        task = runtime.create_task(
            title=f"验收任务 {index}",
            input={
                "taskGoal": intent,
                "usePlanner": True,
                "planningMode": "dynamic",
            },
        )
        _, blueprint = _plan(runtime, task.task_id)
        topologies.append(
            frozenset(step.capability for step in blueprint.step_nodes())
        )

    assert len(set(topologies)) >= 3
    assert all("artifact_generation" in topology for topology in topologies)
