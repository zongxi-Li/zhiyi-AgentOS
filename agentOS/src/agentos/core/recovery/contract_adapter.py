"""Lossless payload preparation for the contract-repair recovery recipe."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any

from agentos.core.data_contracts import (
    ContextContractError,
    apply_contract_defaults,
    validate_contract_payload,
)
from agentos.core.runtime_graph import RuntimeEventType


VALIDATED_LOSSLESS = "validated_lossless"
REGENERATION_REQUIRED = "regeneration_required"
UNREPAIRABLE = "unrepairable"


def payload_hash(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def normalize_payload_shape(payload: Any, schema: dict[str, Any]) -> Any:
    """Apply the one unambiguous envelope transform supported by Core.

    Models occasionally return one array item as the root object even though
    the contract asks for ``{"items": [...]}``.  Wrapping that object is
    lossless when the schema has exactly one required array envelope and the
    item already contains all required fields.
    """

    if not isinstance(payload, dict):
        return deepcopy(payload)
    properties = schema.get("properties")
    required = schema.get("required")
    if not isinstance(properties, dict) or not isinstance(required, list):
        return deepcopy(payload)
    required_envelopes = [
        field
        for field in required
        if isinstance(properties.get(field), dict)
        and properties[field].get("type") == "array"
    ]
    if len(required) != 1 or len(required_envelopes) != 1:
        return deepcopy(payload)
    envelope = required_envelopes[0]
    if envelope in payload:
        return deepcopy(payload)
    item_schema = properties[envelope].get("items")
    if not isinstance(item_schema, dict) or item_schema.get("type") != "object":
        return deepcopy(payload)
    item_required = item_schema.get("required")
    if not isinstance(item_required, list) or not item_required:
        return deepcopy(payload)
    if not set(item_required).issubset(payload):
        return deepcopy(payload)
    return {envelope: [deepcopy(payload)]}


def repair_payload(payload: Any, schema: dict[str, Any]) -> dict[str, Any]:
    """Return an audited, lossless repair decision.

    The adapter may only wrap an unambiguous envelope and apply explicit JSON
    Schema defaults.  It never invents required strings, enum values, numbers,
    booleans, objects, or array items.
    """

    original = deepcopy(payload)
    original_hash = payload_hash(original)
    operations: list[dict[str, str]] = []
    try:
        shaped = normalize_payload_shape(original, schema)
        if shaped != original:
            operations.append({"operation": "wrap_single_required_array"})
        candidate = apply_contract_defaults(shaped, schema)
        if candidate != shaped:
            operations.append({"operation": "apply_explicit_schema_defaults"})
        validate_contract_payload(
            candidate,
            schema,
            step_id="contract_adapter",
            direction="payload",
        )
    except ContextContractError as exc:
        return {
            "adapter_status": REGENERATION_REQUIRED,
            "adapter_operations": operations,
            "adapter_issues": [str(exc)],
            "original_payload_hash": original_hash,
        }
    except Exception as exc:
        return {
            "adapter_status": UNREPAIRABLE,
            "adapter_operations": operations,
            "adapter_issues": [f"{type(exc).__name__}: {exc}"],
            "original_payload_hash": original_hash,
        }

    if candidate == original:
        return {
            "adapter_status": REGENERATION_REQUIRED,
            "adapter_operations": [],
            "adapter_issues": [
                "Payload already satisfies the schema; no lossless repair operation applies."
            ],
            "original_payload_hash": original_hash,
        }
    return {
        "adapter_status": VALIDATED_LOSSLESS,
        "repair_kind": "shape_only",
        "adapter_operations": operations,
        "adapter_issues": [],
        "original_payload_hash": original_hash,
        "adapted_payload_hash": payload_hash(candidate),
        "adapted_payload": candidate,
    }


def _adapter_source_event(context):
    graph = context.run.runtime_graph
    if graph is None:
        return None, None, "runtime_graph_unavailable"
    try:
        adapter_node = graph.get_node(context.step.step_id)
    except KeyError:
        return graph, None, "adapter_node_unavailable"
    patch_id = adapter_node.source_patch_id or str(
        (adapter_node.spec.get("metadata") or {}).get("sourcePatchId") or ""
    )
    if not patch_id:
        return graph, None, "source_patch_unavailable"
    patch = next(
        (item for item in graph.applied_patches if item.patch_id == patch_id),
        None,
    )
    if patch is None:
        return graph, None, "source_patch_unavailable"
    event = graph.runtime_event_by_id(patch.source_event_id)
    if event is None:
        return graph, None, "source_event_unavailable"
    return graph, event, ""


def prepare_contract_repair(context) -> dict[str, Any]:
    """Prepare one repair strictly from the recovery node's source attempt."""

    graph, event, error = _adapter_source_event(context)
    if graph is None or event is None:
        return {
            "adapter_direction": "input",
            "adapter_status": UNREPAIRABLE,
            "adapter_issues": [error],
        }
    if event.event_type not in {
        RuntimeEventType.INPUT_CONTRACT_VIOLATION,
        RuntimeEventType.OUTPUT_CONTRACT_VIOLATION,
    }:
        return {
            "adapter_direction": "input",
            "adapter_status": UNREPAIRABLE,
            "adapter_source_event_id": event.event_id,
            "adapter_issues": ["source_event_is_not_a_contract_violation"],
        }

    target = graph.get_node(event.target_node_id)
    attempt = next(
        (item for item in target.attempts if item.attempt_id == event.attempt_id),
        None,
    )
    if attempt is None:
        return {
            "adapter_direction": "input",
            "adapter_target_node_id": target.node_id,
            "adapter_source_event_id": event.event_id,
            "adapter_source_attempt_id": event.attempt_id,
            "adapter_status": UNREPAIRABLE,
            "adapter_issues": ["source_attempt_unavailable"],
        }

    direction = (
        "output"
        if event.event_type == RuntimeEventType.OUTPUT_CONTRACT_VIOLATION
        else "input"
    )
    if direction == "output":
        payload = deepcopy(attempt.output)
        schema = target.spec.get("outputSpec") or {}
    else:
        payload = deepcopy(attempt.resolved_input)
        input_spec = target.spec.get("inputSpec") or {}
        schema = (
            input_spec.get("schema")
            if isinstance(input_spec.get("schema"), dict)
            else {}
        )

    decision = repair_payload(payload, schema)
    result = {
        **decision,
        "adapter_direction": direction,
        "adapter_target_node_id": target.node_id,
        "adapter_source_event_id": event.event_id,
        "adapter_source_attempt_id": attempt.attempt_id,
    }
    if direction == "output" and str(target.spec.get("capability") or "") == "artifact_generation":
        result.pop("adapted_payload", None)
        result.pop("adapted_payload_hash", None)
        result["adapter_status"] = REGENERATION_REQUIRED
        result["adapter_operations"] = []
        result["adapter_issues"] = [
            "Artifact output requires capability-owned semantic regeneration."
        ]
    return result


__all__ = [
    "REGENERATION_REQUIRED",
    "UNREPAIRABLE",
    "VALIDATED_LOSSLESS",
    "normalize_payload_shape",
    "payload_hash",
    "prepare_contract_repair",
    "repair_payload",
]
