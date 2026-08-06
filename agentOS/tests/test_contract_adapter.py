from copy import deepcopy

import pytest

from agentos.core.recovery.contract_adapter import (
    REGENERATION_REQUIRED,
    VALIDATED_LOSSLESS,
    normalize_payload_shape,
    repair_payload,
)


@pytest.mark.parametrize(
    "schema",
    [
        {
            "type": "object",
            "properties": {"status": {"type": "string", "enum": ["passed", "partial"]}},
            "required": ["status"],
        },
        {
            "type": "object",
            "properties": {"report": {"type": "string", "minLength": 1}},
            "required": ["report"],
        },
        {
            "type": "object",
            "properties": {"count": {"type": "integer"}},
            "required": ["count"],
        },
        {
            "type": "object",
            "properties": {"approved": {"type": "boolean"}},
            "required": ["approved"],
        },
        {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "minItems": 1,
                    "items": {"type": "string"},
                }
            },
            "required": ["items"],
        },
    ],
)
def test_contract_adapter_never_invents_required_semantics(schema):
    result = repair_payload({}, schema)

    assert result["adapter_status"] == REGENERATION_REQUIRED
    assert "adapted_payload" not in result


def test_contract_adapter_enum_order_does_not_create_a_status():
    first = repair_payload(
        {},
        {
            "type": "object",
            "properties": {"status": {"type": "string", "enum": ["passed", "failed"]}},
            "required": ["status"],
        },
    )
    second = repair_payload(
        {},
        {
            "type": "object",
            "properties": {"status": {"type": "string", "enum": ["failed", "passed"]}},
            "required": ["status"],
        },
    )

    assert first["adapter_status"] == second["adapter_status"] == REGENERATION_REQUIRED
    assert "adapted_payload" not in first
    assert "adapted_payload" not in second


def test_contract_adapter_wraps_one_unambiguous_array_item_losslessly():
    payload = {"id": "item-1", "name": "Known item"}
    original = deepcopy(payload)
    schema = {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                    },
                    "required": ["id", "name"],
                },
            }
        },
        "required": ["items"],
    }

    result = repair_payload(payload, schema)

    assert payload == original
    assert result["adapter_status"] == VALIDATED_LOSSLESS
    assert result["repair_kind"] == "shape_only"
    assert result["adapted_payload"] == {"items": [payload]}
    assert normalize_payload_shape(result["adapted_payload"], schema) == result["adapted_payload"]


def test_contract_adapter_only_applies_explicit_schema_defaults():
    result = repair_payload(
        {"report": "Known report"},
        {
            "type": "object",
            "properties": {
                "report": {"type": "string", "minLength": 1},
                "format": {"type": "string", "default": "markdown"},
            },
            "required": ["report", "format"],
        },
    )

    assert result["adapter_status"] == VALIDATED_LOSSLESS
    assert result["adapted_payload"] == {
        "report": "Known report",
        "format": "markdown",
    }
    assert result["adapter_operations"] == [
        {"operation": "apply_explicit_schema_defaults"}
    ]
