"""Deterministic payload preparation for the contract-repair recovery recipe."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from agentos.core.runtime_graph import RuntimeEventType


def _default_value(schema: dict[str, Any]) -> Any:
    if "default" in schema:
        return deepcopy(schema["default"])
    enum = schema.get("enum")
    if isinstance(enum, list) and enum:
        return deepcopy(enum[0])
    value_type = schema.get("type")
    if value_type == "object" or isinstance(schema.get("properties"), dict):
        return repair_payload({}, schema)
    if value_type == "array":
        item_schema = schema.get("items") if isinstance(schema.get("items"), dict) else {}
        return [
            _default_value(item_schema)
            for _ in range(max(0, int(schema.get("minItems") or 0)))
        ]
    if value_type == "string":
        return "unknown" if int(schema.get("minLength") or 0) > 0 else ""
    if value_type in {"number", "integer"}:
        return schema.get("minimum", 0)
    if value_type == "boolean":
        return False
    return None


def repair_payload(payload: Any, schema: dict[str, Any]) -> Any:
    """Coerce only the bounded JSON-Schema shape needed for one retry."""

    value_type = schema.get("type")
    if value_type == "object" or isinstance(schema.get("properties"), dict):
        normalized = dict(payload) if isinstance(payload, dict) else {}
        properties = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
        for field, field_schema in properties.items():
            if not isinstance(field_schema, dict):
                continue
            if field in normalized:
                normalized[field] = repair_payload(normalized[field], field_schema)
            elif field in (schema.get("required") or []) or "default" in field_schema:
                normalized[field] = _default_value(field_schema)
        return normalized
    if value_type == "array":
        normalized = list(payload) if isinstance(payload, list) else []
        item_schema = schema.get("items") if isinstance(schema.get("items"), dict) else {}
        normalized = [repair_payload(item, item_schema) for item in normalized]
        minimum = max(0, int(schema.get("minItems") or 0))
        normalized.extend(_default_value(item_schema) for _ in range(minimum - len(normalized)))
        return normalized
    if value_type == "string" and not isinstance(payload, str):
        return str(payload) if payload is not None else _default_value(schema)
    if value_type == "string" and not payload and int(schema.get("minLength") or 0) > 0:
        return _default_value(schema)
    if value_type == "integer" and not isinstance(payload, int):
        return _default_value(schema)
    if value_type == "number" and not isinstance(payload, (int, float)):
        return _default_value(schema)
    if value_type == "boolean" and not isinstance(payload, bool):
        return _default_value(schema)
    if isinstance(schema.get("enum"), list) and payload not in schema["enum"]:
        return _default_value(schema)
    return deepcopy(payload)


def normalize_payload_shape(payload: Any, schema: dict[str, Any]) -> Any:
    """Repair an unambiguous model envelope without inventing semantic data.

    Models occasionally return one array item as the root object even though
    the contract asks for ``{"items": [...]}``.  When the schema has exactly
    one required array envelope and the payload already satisfies the item's
    required fields, wrapping it is deterministic and safer than adding a
    runtime adapter subgraph.
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


def prepare_contract_repair(context) -> dict[str, Any]:
    graph = context.run.runtime_graph
    if graph is None:
        return {
            "adapted_payload": {},
            "adapter_direction": "input",
            "adapter_status": "target_unavailable",
        }
    event = next(
        (
            item
            for item in reversed(graph.runtime_events)
            if item.target_node_id
            and item.event_type
            in {
                RuntimeEventType.INPUT_CONTRACT_VIOLATION,
                RuntimeEventType.OUTPUT_CONTRACT_VIOLATION,
            }
            and item.status.value == "PROCESSED"
        ),
        None,
    )
    if event is None:
        return {
            "adapted_payload": {},
            "adapter_direction": "input",
            "adapter_status": "event_unavailable",
        }
    target = graph.get_node(event.target_node_id)
    direction = (
        "output"
        if event.event_type == RuntimeEventType.OUTPUT_CONTRACT_VIOLATION
        else "input"
    )
    if direction == "output":
        payload = dict(target.attempts[-1].output) if target.attempts else {}
        schema = target.spec.get("outputSpec") or {}
    else:
        payload: dict[str, Any] = {}
        for node in graph.nodes:
            if node.status.value == "completed" and isinstance(node.output, dict):
                payload.update(node.output)
        if target.attempts:
            payload.update(target.attempts[-1].resolved_input)
        input_spec = target.spec.get("inputSpec") or {}
        schema = input_spec.get("schema") if isinstance(input_spec.get("schema"), dict) else {}
    return {
        "adapted_payload": repair_payload(payload, schema),
        "adapter_direction": direction,
        "adapter_target_node_id": target.node_id,
        "adapter_status": "prepared",
    }


__all__ = ["normalize_payload_shape", "prepare_contract_repair", "repair_payload"]
