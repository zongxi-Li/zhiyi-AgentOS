from agentos.core.acg import ACGBlueprint, StepNode
from agentos.core.execution.acg_executor import ACGExecutor
from agentos.core.execution.projection import refresh_run_execution_projection
from agentos.core.models.types import AgentTask, StepStatus, WorkflowRun, WorkflowStatus
from agentos.core.runtime import WorkflowRuntime
from agentos.core.runtime_graph import RuntimeAttempt, RuntimeGraph
from agentos.stores.sqlite_workflow_store import SQLiteWorkflowStore


class _NullableCodeError(Exception):
    code = None


def test_nullable_exception_code_falls_back_to_exception_type():
    assert ACGExecutor._exception_code(_NullableCodeError("timeout")) == (
        "_NullableCodeError"
    )


async def test_managed_failure_terminalizes_active_graph_before_sqlite_save(tmp_path):
    store = SQLiteWorkflowStore(tmp_path / "managed-failure.db")
    runtime = WorkflowRuntime(workflow_store=store)
    task = AgentTask(
        taskId="task_failure",
        title="managed failure",
        status=WorkflowStatus.RUNNING,
    )
    store.save_task(task)
    blueprint = ACGBlueprint(
        graphId="graph_failure",
        nodes=[StepNode(nodeId="active", agentName="worker", capability="work")],
    )
    graph = RuntimeGraph.from_blueprint(run_id="run_failure", blueprint=blueprint)
    node = graph.get_node("active")
    node.status = StepStatus.RUNNING
    node.attempts.append(
        RuntimeAttempt(
            attemptId="attempt_failure",
            attemptNumber=1,
            graphVersion=graph.graph_version,
            status=StepStatus.RUNNING,
        )
    )
    run = WorkflowRun(
        runId="run_failure",
        taskId=task.task_id,
        workflowId="workflow_failure",
        domain="general",
        runtimeEngine="acg",
        status=WorkflowStatus.RUNNING,
        runtimeGraph=graph,
    )
    refresh_run_execution_projection(run)
    store.save_run(run)

    failed = await runtime.fail_run_safely(
        run.run_id,
        error_code="APITimeoutError",
        error_message="Request timed out.",
    )
    reloaded = store.get_run(run.run_id)
    failed_node = reloaded.runtime_graph.get_node("active")

    assert failed.status == WorkflowStatus.FAILED
    assert reloaded.status == WorkflowStatus.FAILED
    assert failed_node.status == StepStatus.FAILED
    assert failed_node.attempts[-1].status == StepStatus.FAILED
    assert failed_node.attempts[-1].ended_at is not None
    assert reloaded.active_step_ids == []
    assert reloaded.error == {
        "code": "APITimeoutError",
        "message": "Request timed out.",
    }
