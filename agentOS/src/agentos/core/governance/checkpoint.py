"""AgentOS Core 的 checkpoint 模块，提供运行时控制、状态、Trace、审核或治理能力。"""


from typing import Any, Dict, List
from agentos.core.models.types import Checkpoint, WorkflowRun


class CheckpointStore:
    """创建并查询内存中的工作流检查点。"""

    def create(self, run: WorkflowRun, step_id: str) -> Checkpoint:
        blueprint = run.acg_blueprint or {}
        runtime_graph = run.runtime_graph
        graph_version = runtime_graph.graph_version if runtime_graph is not None else None
        graph_id = (
            runtime_graph.graph_id
            if runtime_graph is not None
            else (blueprint.get("graphId") if isinstance(blueprint, dict) else None)
        )
        completed_ids = sorted(
            set(run.completed_step_ids)
            | {step.step_id for step in run.steps if step.status.value == "completed"}
        )
        state_snapshot: Dict[str, Any] = {
            "runId": run.run_id,
            "taskId": run.task_id,
            "workflowId": run.workflow_id,
            "domain": run.domain,
            "status": run.status.value,
            "currentStepId": run.current_step_id,
            "reviewMode": run.review_mode,
            "input": run.input,
            "output": run.output,
            "steps": [step.model_dump(by_alias=True, mode="json") for step in run.steps],
            "acgBlueprint": run.acg_blueprint,
            "runtimeGraph": (
                runtime_graph.model_dump(by_alias=True, mode="json")
                if runtime_graph is not None
                else None
            ),
            "completedStepIds": completed_ids,
            "pendingStepIds": sorted(
                step.step_id for step in run.steps if step.step_id not in completed_ids
            ),
            "activeStepIds": list(run.active_step_ids),
            "provenance": run.provenance,
            "executionState": dict(run.execution_state),
            "enabledPluginIds": list(run.enabled_plugin_ids),
            "resolvedEnabledPluginIds": list(run.resolved_enabled_plugin_ids),
            "pluginSnapshot": [
                item.model_dump(by_alias=True, mode="json")
                for item in run.plugin_snapshot
            ],
            "capabilityCatalogRevision": run.capability_catalog_revision,
            "executionScope": (
                run.execution_scope.model_dump(by_alias=True, mode="json")
                if run.execution_scope is not None
                else None
            ),
            "workflowVersion": run.execution_state.get("workflowVersion"),
            "graphId": graph_id,
            "graphVersion": graph_version,
            "appliedPatchIds": (
                list(runtime_graph.applied_patch_ids) if runtime_graph is not None else []
            ),
            "runtimeEvents": (
                [
                    event.model_dump(by_alias=True, mode="json")
                    for event in runtime_graph.runtime_events
                ]
                if runtime_graph is not None
                else []
            ),
            "pendingRuntimeEventIds": (
                list(runtime_graph.pending_runtime_event_ids)
                if runtime_graph is not None
                else []
            ),
            "processedEventIds": (
                list(runtime_graph.processed_event_ids)
                if runtime_graph is not None
                else []
            ),
            "eventToPatch": (
                dict(runtime_graph.event_to_patch) if runtime_graph is not None else {}
            ),
            "branchDecisions": (
                [
                    item.model_dump(by_alias=True, mode="json")
                    for item in runtime_graph.branch_decisions
                ]
                if runtime_graph is not None
                else []
            ),
            "conditionalDecisionCount": (
                len(runtime_graph.branch_decisions) if runtime_graph is not None else 0
            ),
        }
        checkpoint = Checkpoint(
            runId=run.run_id,
            stepId=step_id,
            stateSnapshot=state_snapshot,
            outputSnapshot=dict(run.get_step(step_id).output),
            canResume=True,
        )
        run.checkpoints.append(checkpoint)
        return checkpoint

    def find(self, run: WorkflowRun, checkpoint_id: str) -> Checkpoint:
        for checkpoint in run.checkpoints:
            if checkpoint.checkpoint_id == checkpoint_id:
                return checkpoint
        raise KeyError(f"checkpoint not found: {checkpoint_id}")

    def list(self, run: WorkflowRun) -> List[Checkpoint]:
        return sorted(run.checkpoints, key=lambda checkpoint: (checkpoint.created_at, checkpoint.checkpoint_id))
