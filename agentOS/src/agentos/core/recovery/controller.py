"""Single-writer controller for versioned RuntimeGraph structure changes."""

from __future__ import annotations

from agentos.core.acg.blueprint import ACGBlueprint
from agentos.core.governance.checkpoint import CheckpointStore
from agentos.core.governance.trace import TraceStore
from agentos.core.execution.projection import refresh_run_execution_projection
from agentos.core.models.enums import StepStatus
from agentos.core.models.types import TraceEventType, utc_now
from agentos.core.recovery.errors import PatchConflictError, RuntimeGraphError
from agentos.core.recovery.models import PatchApplyResult, RuntimeGraphPatch
from agentos.core.recovery.validator import PatchValidator
from agentos.core.run_locks import GLOBAL_RUN_LOCK_MANAGER, RunLockManager
from agentos.core.runtime_graph import AppliedPatchRecord, RuntimeGraph
from agentos.core.workflow.state_machine import StateMachine


class RuntimeController:
    """Initialize, load, and atomically persist runtime graph mutations."""

    def __init__(
        self,
        *,
        workflow_store,
        agent_registry,
        checkpoint_store: CheckpointStore,
        trace_store: TraceStore,
        lock_manager: RunLockManager = GLOBAL_RUN_LOCK_MANAGER,
        validator: PatchValidator | None = None,
    ) -> None:
        self.workflow_store = workflow_store
        self.agent_registry = agent_registry
        self.checkpoint_store = checkpoint_store
        self.trace_store = trace_store
        self.lock_manager = lock_manager
        self.validator = validator or PatchValidator(agent_registry)
        self.state_machine = StateMachine()

    def transition_node_state(self, node, target: StepStatus) -> None:
        """Apply the shared Step state machine to an authoritative RuntimeNode."""

        node.status = self.state_machine.transition(node.status, target)
        node.updated_at = utc_now()

    @staticmethod
    def refresh_execution_projection(run) -> None:
        refresh_run_execution_projection(run)

    async def initialize_from_blueprint(
        self,
        run_id: str,
        blueprint: ACGBlueprint,
    ) -> RuntimeGraph:
        """Idempotently persist RuntimeGraph v1 from an immutable blueprint view."""

        async with self.lock_manager.lock_for(run_id):
            run = self.workflow_store.get_run(run_id)
            if run.runtime_graph is not None:
                return run.runtime_graph.model_copy(deep=True)
            candidate = run.model_copy(deep=True)
            candidate.runtime_graph = RuntimeGraph.from_blueprint(
                run_id=run_id,
                blueprint=blueprint.model_copy(deep=True),
                agent_registry=self.agent_registry,
                domain=run.domain,
            )
            self._import_legacy_execution_state(candidate)
            refresh_run_execution_projection(candidate)
            candidate.execution_state["graphId"] = candidate.runtime_graph.graph_id
            candidate.execution_state["graphVersion"] = (
                candidate.runtime_graph.graph_version
            )
            candidate.execution_state["sourceBlueprintVersion"] = (
                candidate.runtime_graph.source_blueprint_version
            )
            candidate.updated_at = utc_now()
            self.workflow_store.save_run(candidate)
            return candidate.runtime_graph.model_copy(deep=True)

    async def load(self, run_id: str) -> RuntimeGraph:
        """Load the latest graph, explicitly initializing legacy ACG runs once."""

        async with self.lock_manager.lock_for(run_id):
            run = self.workflow_store.get_run(run_id)
            if run.runtime_graph is not None:
                return run.runtime_graph.model_copy(deep=True)
            if not run.acg_blueprint:
                raise RuntimeGraphError(
                    "RUNTIME_GRAPH_MISSING", "run has no ACG blueprint"
                )
            blueprint = ACGBlueprint.model_validate(run.acg_blueprint)
            candidate = run.model_copy(deep=True)
            candidate.runtime_graph = RuntimeGraph.from_blueprint(
                run_id=run_id,
                blueprint=blueprint,
                agent_registry=self.agent_registry,
                domain=run.domain,
            )
            self._import_legacy_execution_state(candidate)
            refresh_run_execution_projection(candidate)
            candidate.execution_state["graphId"] = candidate.runtime_graph.graph_id
            candidate.execution_state["graphVersion"] = (
                candidate.runtime_graph.graph_version
            )
            candidate.execution_state["sourceBlueprintVersion"] = (
                candidate.runtime_graph.source_blueprint_version
            )
            candidate.updated_at = utc_now()
            self.workflow_store.save_run(candidate)
            return candidate.runtime_graph.model_copy(deep=True)

    async def apply_patch(
        self, run_id: str, patch: RuntimeGraphPatch
    ) -> PatchApplyResult:
        """Apply one patch under the shared run lock and persist exactly once."""

        async with self.lock_manager.lock_for(run_id):
            latest = self.workflow_store.get_run(run_id)
            candidate_run, result = self.apply_patch_to_candidate(latest, patch)
            if not result.applied:
                return result
            checkpoint = self.create_patch_checkpoint(candidate_run, patch)
            result.checkpoint_id = checkpoint.checkpoint_id
            result.runtime_graph = candidate_run.runtime_graph.model_copy(deep=True)
            self.workflow_store.save_run(candidate_run)
            return result

    def apply_patch_to_candidate(
        self,
        loaded_run,
        patch: RuntimeGraphPatch,
    ) -> tuple[object, PatchApplyResult]:
        """Apply to a deep run copy without locking or saving; callers own the barrier lock."""

        graph = loaded_run.runtime_graph
        if graph is None:
            raise RuntimeGraphError(
                "RUNTIME_GRAPH_MISSING", "initialize the run before patching"
            )
        replay = self._check_replay(graph, patch)
        if replay is not None:
            return loaded_run.model_copy(deep=True), replay
        if patch.source_event_id in graph.processed_event_ids:
            raise PatchConflictError(
                "EVENT_ALREADY_PROCESSED",
                f"source event {patch.source_event_id} already produced a patch",
            )
        if patch.base_graph_version != graph.graph_version:
            raise PatchConflictError(
                "GRAPH_VERSION_CONFLICT",
                f"expected graphVersion {graph.graph_version}, got {patch.base_graph_version}",
            )

        candidate_run = loaded_run.model_copy(deep=True)
        candidate_graph = self.validator.validate(
            candidate_run.runtime_graph,
            patch,
            domain=candidate_run.domain,
        )
        candidate_graph.graph_version += 1
        candidate_graph.updated_at = utc_now()
        candidate_graph.processed_event_ids.append(patch.source_event_id)
        candidate_graph.applied_patch_ids.append(patch.patch_id)
        candidate_graph.applied_patch_idempotency_keys.append(patch.idempotency_key)
        recipe_id = str(patch.metadata.get("recipeId") or "")
        if recipe_id:
            scope = candidate_graph.recipe_scope(recipe_id, patch.target_node_id)
            if scope not in candidate_graph.applied_recipe_scopes:
                candidate_graph.applied_recipe_scopes.append(scope)
        record = AppliedPatchRecord(
            patchId=patch.patch_id,
            idempotencyKey=patch.idempotency_key,
            contentHash=patch.content_hash(),
            semanticHash=patch.semantic_hash(),
            operationType=patch.operation_type.value,
            baseGraphVersion=patch.base_graph_version,
            resultGraphVersion=candidate_graph.graph_version,
            sourceEventId=patch.source_event_id,
        )
        candidate_graph.applied_patches.append(record)
        candidate_run.runtime_graph = candidate_graph
        refresh_run_execution_projection(candidate_run)
        candidate_run.execution_state["graphId"] = candidate_graph.graph_id
        candidate_run.execution_state["graphVersion"] = candidate_graph.graph_version
        candidate_run.execution_state["sourceBlueprintVersion"] = (
            candidate_graph.source_blueprint_version
        )
        candidate_run.updated_at = utc_now()
        self.trace_store.append(
            run=candidate_run,
            event_type=(
                TraceEventType.GRAPH_PATCH_APPLIED
                if recipe_id
                else TraceEventType.RUNTIME_PATCH_APPLIED
            ),
            observation=f"Applied runtime graph patch {patch.patch_id}",
            step_id=patch.target_node_id,
            payload={
                "eventId": patch.source_event_id,
                "proposalId": patch.proposal_id,
                "patchId": patch.patch_id,
                "recipeId": recipe_id,
                "baseGraphVersion": patch.base_graph_version,
                "resultGraphVersion": candidate_graph.graph_version,
                "runtimeNodeId": patch.target_node_id,
                "targetNodeId": patch.target_node_id,
            },
        )
        return candidate_run, PatchApplyResult(
            applied=True,
            idempotentReplay=False,
            graphVersion=candidate_graph.graph_version,
            patchId=patch.patch_id,
            runtimeGraph=candidate_graph.model_copy(deep=True),
        )

    def create_patch_checkpoint(self, candidate_run, patch: RuntimeGraphPatch):
        """Create the patch checkpoint after event state/mapping has been finalized."""

        graph = candidate_run.runtime_graph
        assert graph is not None
        checkpoint = self.checkpoint_store.create(candidate_run, patch.target_node_id)
        record = graph.patch_record_by_id(patch.patch_id)
        assert record is not None
        record.checkpoint_id = checkpoint.checkpoint_id
        checkpoint.state_snapshot["runtimeGraph"] = graph.model_dump(by_alias=True, mode="json")
        checkpoint.state_snapshot["appliedPatchIds"] = list(graph.applied_patch_ids)
        self.trace_store.append(
            run=candidate_run,
            event_type=TraceEventType.CHECKPOINT_CREATED,
            observation=f"Checkpoint created after patch {patch.patch_id}",
            step_id=patch.target_node_id,
            payload={
                "checkpointId": checkpoint.checkpoint_id,
                "graphVersion": graph.graph_version,
                "eventId": patch.source_event_id,
                "patchId": patch.patch_id,
            },
        )
        return checkpoint

    @staticmethod
    def _check_replay(
        graph: RuntimeGraph,
        patch: RuntimeGraphPatch,
    ) -> PatchApplyResult | None:
        by_id = graph.patch_record_by_id(patch.patch_id)
        if by_id is not None:
            if by_id.content_hash != patch.content_hash():
                raise PatchConflictError(
                    "PATCH_ID_CONTENT_CONFLICT",
                    f"patchId {patch.patch_id} was applied with different content",
                )
            return PatchApplyResult(
                applied=False,
                idempotentReplay=True,
                graphVersion=by_id.result_graph_version,
                patchId=by_id.patch_id,
                checkpointId=by_id.checkpoint_id,
                runtimeGraph=graph.model_copy(deep=True),
            )

        by_key = graph.patch_record_by_idempotency_key(patch.idempotency_key)
        if by_key is not None:
            if by_key.semantic_hash != patch.semantic_hash():
                raise PatchConflictError(
                    "IDEMPOTENCY_KEY_CONTENT_CONFLICT",
                    f"idempotencyKey {patch.idempotency_key} was used for different semantics",
                )
            return PatchApplyResult(
                applied=False,
                idempotentReplay=True,
                graphVersion=by_key.result_graph_version,
                patchId=by_key.patch_id,
                checkpointId=by_key.checkpoint_id,
                runtimeGraph=graph.model_copy(deep=True),
            )
        return None

    @staticmethod
    def _import_legacy_execution_state(run) -> None:
        """One-time compatibility import used only while initializing an old run."""

        graph = run.runtime_graph
        if graph is None:
            return
        legacy = {step.step_id: step for step in run.steps}
        for node in graph.nodes:
            step = legacy.get(node.node_id)
            if step is None:
                continue
            node.status = step.status
            node.output = dict(step.output)
            node.output_version = 1 if step.output else 0
            node.error = step.error


__all__ = ["RuntimeController"]
