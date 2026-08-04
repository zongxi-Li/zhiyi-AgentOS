from agentos.core.acg import ACGBlueprint, StepNode
from agentos.core.execution.package import StepExecutionOutcome
from agentos.core.models.types import StepStatus, utc_now
from agentos.core.recovery import (
    RecoveryRecipeRegistry,
    RuntimeEventClassifier,
    RuntimeEventPolicy,
    RuntimeEventType,
)
from agentos.core.runtime_graph import RuntimeAttempt, RuntimeGraph


def _graph(errors: list[str], *, retry_limit: int = 3) -> RuntimeGraph:
    graph = RuntimeGraph.from_blueprint(
        run_id="run_1",
        blueprint=ACGBlueprint(
            graphId="graph_1",
            nodes=[StepNode(nodeId="target", capability="work", retryLimit=retry_limit)],
        ),
    )
    node = graph.get_node("target")
    node.current_binding = {
        "bindingId": "binding_a",
        "agentName": "a",
        "domain": "test",
        "capability": "work",
    }
    for index, error in enumerate(errors, start=1):
        node.attempts.append(
            RuntimeAttempt(
                attemptNumber=index,
                graphVersion=1,
                bindingId="binding_a",
                agentName="a",
                status=StepStatus.FAILED,
                error=error,
            )
        )
    return graph


def _outcome(*, attempt: int, error_type: str, error_code: str):
    return StepExecutionOutcome(
        runId="run_1",
        graphId="graph_1",
        scheduledGraphVersion=1,
        runtimeNodeId="target",
        attemptId=f"attempt_{attempt}",
        status=StepStatus.RETRYING,
        error="safe failure",
        errorType=error_type,
        errorCode=error_code,
        startedAt=utc_now(),
        endedAt=utc_now(),
    )


def test_agent_not_found_immediately_maps_to_binding_patch_policy():
    graph = _graph(["missing"])
    outcome = _outcome(attempt=1, error_type="AgentNotFound", error_code="AgentNotFound")
    event = RuntimeEventClassifier().classify(outcome, graph.get_node("target"), graph)[0]
    decision = RuntimeEventPolicy(RecoveryRecipeRegistry.with_defaults()).decide(event, graph)

    assert event.event_type == RuntimeEventType.BINDING_UNAVAILABLE
    assert event.payload["failedBindingId"] == "binding_a"
    assert decision.patch_operation == "RETRY_ALTERNATE_BINDING"


def test_transient_failure_retries_once_then_switches_and_contract_error_never_switches():
    classifier = RuntimeEventClassifier()
    first_graph = _graph(["timeout"])
    first = classifier.classify(
        _outcome(attempt=1, error_type="TimeoutError", error_code="MODEL_TIMEOUT"),
        first_graph.get_node("target"),
        first_graph,
    )
    assert first[0].event_type == RuntimeEventType.STEP_EXECUTION_FAILED

    second_graph = _graph(["timeout", "timeout"])
    switched = classifier.classify(
        _outcome(attempt=2, error_type="TimeoutError", error_code="MODEL_TIMEOUT"),
        second_graph.get_node("target"),
        second_graph,
    )[0]
    assert switched.event_type == RuntimeEventType.BINDING_UNAVAILABLE
    assert switched.reason_code == "BINDING_RETRY_EXHAUSTED"

    contract = classifier.classify(
        _outcome(attempt=2, error_type="ContextContractError", error_code="MISSING_FIELD"),
        second_graph.get_node("target"),
        second_graph,
    )[0]
    assert contract.event_type == RuntimeEventType.OUTPUT_CONTRACT_VIOLATION

    wrapped_contract = classifier.classify(
        _outcome(
            attempt=2,
            error_type="StructuredGenerationError",
            error_code="OUTPUT_CONTRACT_VIOLATION",
        ),
        second_graph.get_node("target"),
        second_graph,
    )[0]
    assert wrapped_contract.event_type == RuntimeEventType.OUTPUT_CONTRACT_VIOLATION


def test_zero_retry_dynamic_node_switches_binding_after_first_model_failure():
    graph = _graph(["invalid structured output"], retry_limit=0)

    event = RuntimeEventClassifier().classify(
        _outcome(
            attempt=1,
            error_type="StructuredGenerationError",
            error_code="MODEL_OUTPUT_INVALID_JSON",
        ),
        graph.get_node("target"),
        graph,
    )[0]

    assert event.event_type == RuntimeEventType.BINDING_UNAVAILABLE
    assert event.reason_code == "BINDING_RETRY_EXHAUSTED"
