"""RuntimeGraph-authoritative ACG scheduler with snapshot execution barriers."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from agentos.core.acg import ACGBlueprint, AgentNode, EdgeType, StepNode, validate_blueprint
from agentos.core.communication import (
    ContextAssembler,
    ContextContractError,
    ProvenanceLedger,
    validate_contract_payload,
)
from agentos.core.execution.fault_injection import FaultInjector, InjectedFault
from agentos.core.execution.package import StepExecutionOutcome, StepExecutionPackage
from agentos.core.execution.projection import refresh_run_execution_projection
from agentos.core.execution.step_wrapper import StepExecutionTimer, input_summary, output_summary
from agentos.core.models.types import (
    AgentTask,
    StepStatus,
    TraceEventType,
    WorkflowRun,
    WorkflowStatus,
    utc_now,
)
from agentos.core.runtime_graph import RuntimeAttempt, RuntimeGraph, RuntimeNode
from agentos.memory.workflow_memory import WorkflowMemory

if TYPE_CHECKING:
    from agentos.core.runtime import WorkflowRuntime


class ACGExecutor:
    """Schedule RuntimeGraph ready nodes and atomically commit detached outcomes."""

    def __init__(self, runtime: "WorkflowRuntime", *, max_parallelism: int = 4):
        self.runtime = runtime
        self.max_parallelism = max(1, max_parallelism)
        self.fault_injector = FaultInjector()

    async def run(self, *, task: AgentTask, run: WorkflowRun, workflow, blueprint: ACGBlueprint) -> WorkflowRun:
        validate_blueprint(blueprint)
        self.fault_injector = FaultInjector.from_config(task.input.get("faultInjection"))
        async with self.runtime.run_lock_manager.lock_for(run.run_id):
            latest = self.runtime.workflow_store.get_run(run.run_id)
            candidate = latest.model_copy(deep=True)
            candidate.acg_blueprint = blueprint.model_dump(by_alias=True, mode="json")
            candidate.execution_state = {
                **candidate.execution_state,
                "scheduleRound": int(candidate.execution_state.get("scheduleRound", 0)),
                "faultInjectionTriggered": 0,
            }
            self.runtime._transition_run_if_needed(candidate, WorkflowStatus.RUNNING)
            self.runtime.task_manager.mark_running(task)
            self.runtime.trace_store.append(
                run=candidate,
                event_type=TraceEventType.RUN_STARTED,
                observation=f"ACG execution started: {blueprint.graph_id}",
                payload={"graphId": blueprint.graph_id, "nodeCount": blueprint.node_count,
                         "edgeCount": blueprint.edge_count, "engine": "acg"},
            )
            self.runtime.workflow_store.save_run(candidate)
        return await self._drive(task=task, run=candidate, workflow=workflow, blueprint=blueprint)

    async def resume(self, *, task: AgentTask, run: WorkflowRun, workflow, blueprint: ACGBlueprint) -> WorkflowRun:
        validate_blueprint(blueprint)
        self.fault_injector = FaultInjector.from_config(task.input.get("faultInjection"))
        self.fault_injector.restore_triggered_count(
            int(run.execution_state.get("faultInjectionTriggered", 0))
        )
        return await self._drive(task=task, run=run, workflow=workflow, blueprint=blueprint)

    async def _drive(self, *, task, run, workflow, blueprint: ACGBlueprint) -> WorkflowRun:
        """Reload, schedule, execute snapshots, and commit at a batch barrier."""

        run_id = run.run_id  # only identity is retained; every round reloads authority
        while True:
            packages = await self._schedule_batch(task, workflow, run_id)
            if packages is None:
                return self.runtime.workflow_store.get_run(run_id)
            if not packages:
                return self.runtime.workflow_store.get_run(run_id)
            outcomes = await asyncio.gather(
                *(self._execute_package(task, workflow, package) for package in packages)
            )
            should_continue = await self._commit_batch(task, outcomes)
            if not should_continue:
                return self.runtime.workflow_store.get_run(packages[0].run_id)

    async def _schedule_batch(self, task, workflow, run_id: str) -> list[StepExecutionPackage] | None:
        del workflow
        async with self.runtime.run_lock_manager.lock_for(run_id):
            latest = self.runtime.workflow_store.get_run(run_id)
            graph = latest.runtime_graph
            if graph is None:
                raise RuntimeError("RUNTIME_GRAPH_MISSING")
            if latest.status == WorkflowStatus.CANCELLED:
                return None
            candidate = latest.model_copy(deep=True)
            graph = candidate.runtime_graph
            assert graph is not None
            graph.resolve_ready_control_nodes()
            refresh_run_execution_projection(candidate)

            if graph.has_waiting_review():
                self.runtime._transition_run_if_needed(candidate, WorkflowStatus.WAITING_REVIEW)
                self.runtime.workflow_store.save_run(candidate)
                return None
            ready = graph.ready_set()
            if not ready:
                if graph.all_steps_completed():
                    refresh_run_execution_projection(candidate)
                    self.runtime._complete_run(task, candidate)
                    self.runtime.workflow_store.save_run(candidate)
                    return None
                if graph.has_running_nodes():
                    return None
                failed = [node for node in graph.nodes if node.status == StepStatus.FAILED]
                if failed:
                    self.runtime._transition_run_if_needed(candidate, WorkflowStatus.FAILED)
                    self.runtime.task_manager.mark_failed(task)
                    candidate.error = failed[0].error or "runtime node failed"
                else:
                    self.runtime._transition_run_if_needed(candidate, WorkflowStatus.FAILED)
                    self.runtime.task_manager.mark_failed(task)
                    candidate.error = "RUNTIME_GRAPH_DEADLOCK"
                    self.runtime.trace_store.append(
                        run=candidate,
                        event_type=TraceEventType.RUN_FAILED,
                        observation="Runtime graph has no ready, running, or review node",
                        payload={"errorCode": "RUNTIME_GRAPH_DEADLOCK", "graphVersion": graph.graph_version},
                    )
                self.runtime.workflow_store.save_run(candidate)
                return None

            selected = self._select_batch(graph, ready)
            schedule_round = int(candidate.execution_state.get("scheduleRound", 0)) + 1
            candidate.execution_state["scheduleRound"] = schedule_round
            packages: list[StepExecutionPackage] = []
            for node in selected:
                self.runtime.runtime_controller.transition_node_state(node, StepStatus.RUNNING)
                binding = dict(node.current_binding or {})
                binding_id = str(binding.get("assignedAgentId") or binding.get("agentName") or node.node_id)
                attempt = RuntimeAttempt(
                    attemptNumber=len(node.attempts) + 1,
                    graphVersion=graph.graph_version,
                    bindingId=binding_id,
                    agentName=str(binding.get("agentName") or node.spec.get("agentName") or ""),
                    modelName=str(binding.get("modelName") or ""),
                    status=StepStatus.RUNNING,
                )
                node.attempts.append(attempt)
                self.runtime.trace_store.append(
                    run=candidate,
                    event_type=TraceEventType.STEP_SCHEDULED,
                    step_id=node.node_id,
                    agent_name=attempt.agent_name,
                    observation=f"Step scheduled (ready set size={len(ready)})",
                    payload=self._correlation(graph, node, attempt, scheduled=graph.graph_version)
                    | {"readySet": [item.node_id for item in ready],
                       "batch": [item.node_id for item in selected],
                       "batchId": f"batch_{schedule_round:04d}"},
                )
                self.runtime.trace_store.append(
                    run=candidate,
                    event_type=TraceEventType.STEP_STARTED,
                    step_id=node.node_id,
                    agent_name=attempt.agent_name,
                    observation=f"Step started: {node.spec.get('name') or node.node_id}",
                    payload=self._correlation(graph, node, attempt, scheduled=graph.graph_version)
                    | {"inputSummary": input_summary(node.spec.get("inputSpec") or {})},
                )
            refresh_run_execution_projection(candidate)
            candidate.updated_at = utc_now()
            self.runtime.workflow_store.save_run(candidate)

            graph = candidate.runtime_graph
            assert graph is not None
            for node in selected:
                persisted = graph.get_node(node.node_id)
                attempt = persisted.attempts[-1]
                packages.append(self._make_package(candidate, task, persisted, attempt))
            return packages

    def _make_package(self, run, task, node: RuntimeNode, attempt: RuntimeAttempt) -> StepExecutionPackage:
        graph = run.runtime_graph
        assert graph is not None
        source_ids = self._data_sources(graph, node.node_id)
        spec = node.spec.get("inputSpec") or {}
        if not isinstance(spec.get("from"), dict) and not isinstance(spec.get("fields"), list):
            source_ids = [
                item.node_id for item in graph.nodes
                if item.node_id != node.node_id and item.status == StepStatus.COMPLETED and item.output
            ]
        upstream = {source_id: dict(graph.get_node(source_id).output) for source_id in source_ids}
        return StepExecutionPackage(
            runId=run.run_id,
            taskId=task.task_id,
            graphId=graph.graph_id,
            graphVersion=graph.graph_version,
            runtimeNodeId=node.node_id,
            attemptId=attempt.attempt_id,
            attemptNumber=attempt.attempt_number,
            binding=dict(node.current_binding or {}),
            nodeSpec=dict(node.spec),
            runInput=dict(run.input),
            upstreamOutputs=upstream,
            contextMetadata={"objective": ACGBlueprint.model_validate(run.acg_blueprint).objective},
            timeout=int(node.spec.get("timeout") or 0),
            runSnapshot=run.model_dump(by_alias=True, mode="json"),
        )

    async def _execute_package(self, task, workflow, package: StepExecutionPackage) -> StepExecutionOutcome:
        """Perform remote work against a private snapshot and return a detached outcome."""

        started_at = utc_now()
        local_run = WorkflowRun.model_validate(package.run_snapshot)
        graph = local_run.runtime_graph
        assert graph is not None
        node = graph.get_node(package.runtime_node_id)
        step_node = StepNode.model_validate(package.node_spec)
        step = local_run.get_step(package.runtime_node_id)
        binding_id = str(package.binding.get("assignedAgentId") or package.binding.get("agentName") or node.node_id)
        ledger = ProvenanceLedger(run_id=package.run_id, task_id=package.task_id)
        assembler = ContextAssembler(ledger)
        resolved: dict[str, Any] = {}
        pack = None
        timer = StepExecutionTimer()
        try:
            if package.upstream_outputs:
                pack = assembler.assemble(
                    run_id=package.run_id,
                    task_id=package.task_id,
                    runtime_graph=graph,
                    step_node=step_node,
                    objective=str(package.context_metadata.get("objective") or ""),
                    upstream_outputs=package.upstream_outputs,
                    consumer_agent_name=step.agent_name,
                    attempt=package.attempt_number,
                    attempt_id=package.attempt_id,
                    binding_id=binding_id,
                )
                resolved = dict(pack.data)
                step.resolved_input = resolved
            memory = WorkflowMemory.from_context_pack(local_run, pack) if pack else WorkflowMemory(
                run_id=package.run_id, task_input=dict(package.run_input), observations={}
            )
            self.fault_injector.fire(package.runtime_node_id)
            dispatch = self.runtime.orchestrator.dispatch_agent(
                task=task, run=local_run, workflow=workflow, step=step, memory=memory, context_pack=pack
            )
            result, _ = await asyncio.wait_for(dispatch, timeout=package.timeout) if package.timeout > 0 else await dispatch
            output = dict(result.output)
            validate_contract_payload(output, step_node.output_spec, step_id=node.node_id, direction="output")
            status = StepStatus.WAITING_REVIEW if step.requires_review and local_run.review_mode != "auto" else StepStatus.COMPLETED
            events = [
                {"eventType": TraceEventType.DATA_PRODUCED, "observation": f"Data produced by {node.node_id}",
                 "payload": {"fields": sorted(output), "attempt": package.attempt_number}},
                {"eventType": TraceEventType.AGENT_CALLED, "observation": result.summary or f"Agent completed: {step.agent_name}",
                 "payload": output, "durationMs": timer.elapsed_ms()},
                {"eventType": TraceEventType.REVIEW_REQUIRED if status == StepStatus.WAITING_REVIEW else TraceEventType.STEP_SUCCEEDED,
                 "observation": f"Review required for step: {node.node_id}" if status == StepStatus.WAITING_REVIEW else f"Step succeeded: {step.name}",
                 "payload": output if status == StepStatus.WAITING_REVIEW else {"outputSummary": output_summary(output)},
                 "durationMs": timer.elapsed_ms()},
            ]
            if pack is not None:
                events.insert(0, {"eventType": TraceEventType.DATA_CONSUMED,
                    "observation": f"Context assembled: {pack.tokens_delivered}/{pack.tokens_available} tokens (saved {pack.saving_ratio:.1%})",
                    "payload": pack.model_dump(by_alias=True, mode="json")})
            return self._outcome(package, status, started_at, output=output, resolved=resolved,
                                 events=events, provenance={"pack": pack.model_dump(by_alias=True, mode="json") if pack else None})
        except Exception as exc:
            recoverable = isinstance(exc, InjectedFault) or package.attempt_number <= int(step_node.retry_limit)
            event_type = TraceEventType.CONTRACT_VIOLATION if isinstance(exc, ContextContractError) else TraceEventType.STEP_FAILED
            return self._outcome(package, StepStatus.RETRYING if recoverable else StepStatus.FAILED,
                                 started_at, error=str(exc), resolved=resolved, recoverable=recoverable,
                                 events=[{"eventType": event_type, "observation": str(exc),
                                          "payload": {"recoverable": recoverable, "attempt": package.attempt_number}}])

    async def _commit_batch(self, task, outcomes: list[StepExecutionOutcome]) -> bool:
        """Merge all accepted outcomes into one copy and persist once."""

        if not outcomes:
            return False
        run_id = outcomes[0].run_id
        async with self.runtime.run_lock_manager.lock_for(run_id):
            latest = self.runtime.workflow_store.get_run(run_id)
            candidate = latest.model_copy(deep=True)
            graph = candidate.runtime_graph
            assert graph is not None
            ledger = ProvenanceLedger.from_graph(candidate.provenance, run_id=run_id, task_id=task.task_id)
            accepted = False
            accepted_node_ids: set[str] = set()
            waiting_review = False
            fatal = False
            for outcome in outcomes:
                node = graph.get_node(outcome.runtime_node_id)
                attempt = node.attempts[-1] if node.attempts else None
                if candidate.status == WorkflowStatus.CANCELLED:
                    self._late_outcome_trace(candidate, graph, node, outcome, "run cancelled")
                    continue
                if outcome.scheduled_graph_version != graph.graph_version or attempt is None or attempt.attempt_id != outcome.attempt_id or node.status != StepStatus.RUNNING:
                    self._late_outcome_trace(candidate, graph, node, outcome, "stale attempt")
                    continue
                accepted = True
                accepted_node_ids.add(node.node_id)
                attempt.resolved_input = dict(outcome.resolved_input)
                attempt.output = dict(outcome.output)
                attempt.error = outcome.error
                attempt.ended_at = outcome.ended_at
                attempt.status = StepStatus.FAILED if outcome.status == StepStatus.RETRYING else outcome.status
                node.error = outcome.error
                if outcome.output:
                    node.output = dict(outcome.output)
                    node.output_version += 1
                    self._record_degraded_output(candidate, node, attempt, outcome.output)
                self.runtime.runtime_controller.transition_node_state(node, outcome.status)
                for event in outcome.trace_events:
                    self.runtime.trace_store.append(
                        run=candidate, event_type=event["eventType"], step_id=node.node_id,
                        agent_name=attempt.agent_name, observation=event.get("observation", ""),
                        payload=dict(event.get("payload") or {}) | self._correlation(graph, node, attempt, scheduled=outcome.scheduled_graph_version),
                        duration_ms=int(event.get("durationMs") or 0),
                    )
                pack = outcome.provenance_events.get("pack")
                if pack:
                    source_ids = list(pack.get("sourceStepIds") or [])
                    ledger.record_consumption(
                        node.node_id,
                        source_ids,
                        list((pack.get("data") or {}).keys()),
                        consumer_agent_name=attempt.agent_name,
                        attempt=attempt.attempt_number,
                        data=dict(pack.get("data") or {}),
                        tokens_delivered=int(pack.get("tokensDelivered") or 0),
                        tokens_available=int(pack.get("tokensAvailable") or 0),
                        saving_ratio=float(pack.get("savingRatio") or 0.0),
                        contract_status=str(pack.get("contractStatus") or "valid"),
                    )
                    edge_ids = [
                        edge.edge_id
                        for edge in graph.effective_edges(EdgeType.COMMUNICATION)
                        if edge.target_id == node.node_id and edge.source_id in source_ids
                    ]
                    ledger.record_interaction(
                        edge_ids=edge_ids,
                        producer_step_ids=source_ids,
                        consumer_step_id=node.node_id,
                        producer_agent_names=[
                            str((graph.get_node(source_id).current_binding or {}).get("agentName") or "")
                            for source_id in source_ids
                        ],
                        consumer_agent_name=attempt.agent_name,
                        fields_by_producer={
                            source_id: list((pack.get("sourceData") or {}).get(source_id, {}).keys())
                            for source_id in source_ids
                        },
                        tokens_delivered=int(pack.get("tokensDelivered") or 0),
                        tokens_available=int(pack.get("tokensAvailable") or 0),
                        saving_ratio=float(pack.get("savingRatio") or 0.0),
                        evidence_refs=list(pack.get("evidenceRefs") or []),
                        contract_status=str(pack.get("contractStatus") or "valid"),
                        data=dict(pack.get("data") or {}),
                    )
                if outcome.output:
                    ledger.record_production(node.node_id, dict(outcome.output), 0,
                                             agent_name=attempt.agent_name, attempt=attempt.attempt_number)
                if outcome.status == StepStatus.WAITING_REVIEW:
                    waiting_review = True
                elif outcome.status == StepStatus.RETRYING:
                    candidate.recovery_count += 1
                    self.runtime.trace_store.append(
                        run=candidate, event_type=TraceEventType.RUN_RECOVERED, step_id=node.node_id,
                        agent_name=attempt.agent_name, observation=f"Automatic retry scheduled for {node.node_id}",
                        payload=self._correlation(graph, node, attempt, scheduled=outcome.scheduled_graph_version)
                        | {"strategy": "local_replan" if self.fault_injector.triggered_count else "retry"},
                    )
                elif outcome.status == StepStatus.FAILED:
                    fatal = True
            if accepted:
                candidate.provenance = ledger.to_graph()
                candidate.execution_state["faultInjectionTriggered"] = self.fault_injector.triggered_count
                refresh_run_execution_projection(candidate)
                candidate.output = self.runtime.orchestrator.compose_final_output(candidate)
            candidate.updated_at = utc_now()
            if fatal:
                self.runtime._transition_run_if_needed(candidate, WorkflowStatus.FAILED)
                self.runtime.task_manager.mark_failed(task)
                candidate.error = next((node.error for node in graph.nodes if node.status == StepStatus.FAILED), "step failed")
            elif waiting_review:
                self.runtime._transition_run_if_needed(candidate, WorkflowStatus.WAITING_REVIEW)
                self.runtime.task_manager.mark_waiting_review(task)
            elif accepted:
                self.runtime._transition_run_if_needed(candidate, WorkflowStatus.RUNNING)
                self.runtime.task_manager.mark_running(task)
            for outcome in outcomes:
                if outcome.runtime_node_id in accepted_node_ids and outcome.status in {
                    StepStatus.COMPLETED,
                    StepStatus.WAITING_REVIEW,
                    StepStatus.RETRYING,
                }:
                    try:
                        self.runtime._create_checkpoint(candidate, candidate.get_step(outcome.runtime_node_id))
                    except KeyError:
                        pass
            self.runtime.workflow_store.save_run(candidate)
            return accepted and not waiting_review and not fatal and candidate.status != WorkflowStatus.CANCELLED

    def _select_batch(self, graph: RuntimeGraph, ready: list[RuntimeNode]) -> list[RuntimeNode]:
        selected: list[RuntimeNode] = []
        counts: dict[str, int] = {}
        blueprint = graph.to_blueprint()
        for node in ready:
            edges = blueprint.incoming(node.node_id, EdgeType.EXECUTION)
            key = edges[0].source_id if edges else f"step::{node.node_id}"
            limit = 1
            if edges:
                agent = blueprint.get_node(key)
                if isinstance(agent, AgentNode):
                    limit = max(1, agent.max_concurrency)
            if counts.get(key, 0) >= limit:
                continue
            selected.append(node)
            counts[key] = counts.get(key, 0) + 1
            if len(selected) >= self.max_parallelism:
                break
        return selected

    @staticmethod
    def _data_sources(graph: RuntimeGraph, node_id: str) -> list[str]:
        communication = [edge.source_id for edge in graph.effective_edges(EdgeType.COMMUNICATION) if edge.target_id == node_id]
        return list(dict.fromkeys(communication or graph.dependency_sources(node_id)))

    @staticmethod
    def _correlation(graph, node, attempt, *, scheduled: int) -> dict[str, Any]:
        return {"graphVersion": graph.graph_version, "runtimeNodeId": node.node_id,
                "attemptId": attempt.attempt_id, "bindingId": attempt.binding_id,
                "scheduledGraphVersion": scheduled, "attempt": attempt.attempt_number}

    @staticmethod
    def _outcome(package, status, started_at, *, output=None, error=None, resolved=None,
                 events=None, provenance=None, recoverable=False) -> StepExecutionOutcome:
        return StepExecutionOutcome(
            runId=package.run_id, graphId=package.graph_id,
            scheduledGraphVersion=package.graph_version, runtimeNodeId=package.runtime_node_id,
            attemptId=package.attempt_id, status=status, output=output or {}, error=error,
            resolvedInput=resolved or {}, startedAt=started_at, endedAt=utc_now(),
            traceEvents=events or [], provenanceEvents=provenance or {}, recoverable=recoverable,
        )

    def _late_outcome_trace(self, run, graph, node, outcome, reason: str) -> None:
        self.runtime.trace_store.append(
            run=run, event_type=TraceEventType.STEP_FAILED, step_id=node.node_id,
            observation=f"Ignored late execution outcome: {reason}",
            payload={"ignored": True, "reason": reason, "attemptId": outcome.attempt_id,
                     "graphVersion": graph.graph_version, "scheduledGraphVersion": outcome.scheduled_graph_version},
        )

    def _record_degraded_output(self, run, node, attempt, output: dict[str, Any]) -> None:
        llm = output.get("_llm")
        if not isinstance(llm, dict) or llm.get("success") is not False:
            return
        degraded = run.execution_state.setdefault("degradedSteps", [])
        marker = {"stepId": node.node_id, "attempt": attempt.attempt_number}
        if any(
            isinstance(item, dict)
            and item.get("stepId") == marker["stepId"]
            and item.get("attempt") == marker["attempt"]
            for item in degraded
        ):
            return
        detail = {
            **marker,
            "source": str(llm.get("source") or "fallback"),
            "error": str(llm.get("error") or "model output degraded")[:240],
        }
        degraded.append(detail)
        run.recovery_count += 1
        self.runtime.trace_store.append(
            run=run,
            event_type=TraceEventType.RUN_RECOVERED,
            step_id=node.node_id,
            agent_name=attempt.agent_name,
            observation=f"Step used a degraded fallback: {node.spec.get('name') or node.node_id}",
            payload=detail | self._correlation(run.runtime_graph, node, attempt, scheduled=attempt.graph_version),
        )

    def provenance_graph(self) -> dict:
        """Compatibility accessor; persisted provenance is scoped to each run."""

        return {}


__all__ = ["ACGExecutor"]
