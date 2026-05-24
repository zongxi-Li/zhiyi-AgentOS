from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Optional

from app.llm.gateway import get_llm_gateway
from app.graphs.contract_review.state import ContractReviewState


def _copy_state(state: ContractReviewState) -> ContractReviewState:
    return deepcopy(dict(state))


def _append_trace(
    state: ContractReviewState,
    *,
    step_id: str,
    event_type: str,
    observation: str,
    payload: Optional[Dict[str, Any]] = None,
) -> None:
    traces = list(state.get("traces", []))
    traces.append(
        {
            "eventType": event_type,
            "stepId": step_id,
            "agentName": step_id,
            "observation": observation,
            "payload": payload or {},
        }
    )
    state["traces"] = traces


def _set_step(
    state: ContractReviewState,
    step_id: str,
    status: str,
    output: Optional[Dict[str, Any]] = None,
) -> None:
    steps = dict(state.get("steps", {}))
    step = dict(steps.get(step_id, {}))
    step["status"] = status
    if output is not None:
        step["output"] = output
    steps[step_id] = step
    state["steps"] = steps
    state["current_step"] = step_id


def _llm_trace_payload(
    *,
    node_name: str,
    provider: str,
    model: str,
    source: str,
    success: bool,
    latency_ms: int = 0,
    error: Optional[str] = None,
) -> Dict[str, Any]:
    payload = {
        "node_name": node_name,
        "provider": provider,
        "model": model,
        "source": source,
        "success": success,
        "latency_ms": max(0, int(latency_ms or 0)),
    }
    if error:
        payload["error"] = str(error)[:240]
    return payload


def _gateway_json_or_fallback(
    *,
    node_name: str,
    prompt: str,
    schema: Dict[str, Any],
    fallback: Dict[str, Any],
    validator,
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    gateway = get_llm_gateway()
    try:
        response = gateway.generate_json(prompt, schema)
        data = validator(response.get("data", {}))
        provider = str(response.get("provider") or gateway.provider_name)
        source = "mock" if provider == "mock" else "llm"
        return data, _llm_trace_payload(
            node_name=node_name,
            provider=provider,
            model=str(response.get("model") or gateway.model),
            source=source,
            success=True,
            latency_ms=int(response.get("latency_ms") or 0),
        )
    except Exception as exc:
        return fallback, _llm_trace_payload(
            node_name=node_name,
            provider=getattr(gateway, "provider_name", "unknown"),
            model=getattr(gateway, "model", "unknown"),
            source="mock_fallback",
            success=False,
            error=str(exc),
        )
