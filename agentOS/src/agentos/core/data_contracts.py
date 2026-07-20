"""Structured input/output contract validation shared by ACG and communication."""

from __future__ import annotations

from typing import Any, Dict

from jsonschema import ValidationError as JSONSchemaValidationError
from jsonschema.validators import validator_for


class ContextContractError(ValueError):
    """A step input or output does not satisfy its declared JSON Schema."""

    def __init__(self, *, step_id: str, direction: str, message: str, path: str = ""):
        self.step_id = step_id
        self.direction = direction
        self.path = path
        super().__init__(f"{direction} contract violation at {step_id}{f' ({path})' if path else ''}: {message}")


def check_contract_schema(schema: Dict[str, Any], *, label: str) -> None:
    if not schema:
        return
    validator = validator_for(schema)
    try:
        validator.check_schema(schema)
    except Exception as exc:
        raise ValueError(f"invalid JSON Schema for {label}: {exc}") from exc


def validate_contract_payload(
    payload: Any,
    schema: Dict[str, Any],
    *,
    step_id: str,
    direction: str,
) -> None:
    if not schema:
        return
    validator = validator_for(schema)(schema)
    try:
        validator.validate(payload)
    except JSONSchemaValidationError as exc:
        path = ".".join(str(item) for item in exc.absolute_path)
        raise ContextContractError(
            step_id=step_id,
            direction=direction,
            message=exc.message,
            path=path,
        ) from exc


__all__ = ["ContextContractError", "check_contract_schema", "validate_contract_payload"]
