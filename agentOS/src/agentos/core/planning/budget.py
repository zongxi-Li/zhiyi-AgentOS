"""Trusted server-owned coordination budgets for planning."""

from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Mapping

from agentos.core.acg.enums import ComplexityLevel


_DEFAULTS: dict[ComplexityLevel, int] = {
    ComplexityLevel.SIMPLE: 2048,
    ComplexityLevel.MEDIUM: 4096,
    ComplexityLevel.COMPLEX: 8192,
    ComplexityLevel.EXTREME: 16384,
}


@dataclass(frozen=True)
class PlanningBudgetPolicy:
    budgets: Mapping[ComplexityLevel, int]

    @classmethod
    def from_env(cls) -> "PlanningBudgetPolicy":
        values: dict[ComplexityLevel, int] = {}
        for complexity, default in _DEFAULTS.items():
            name = f"AGENTOS_PLANNING_ENTROPY_{complexity.value.upper()}"
            raw = (os.getenv(name) or str(default)).strip()
            try:
                value = int(raw)
            except ValueError as exc:
                raise ValueError(f"{name} must be a positive integer") from exc
            if value <= 0:
                raise ValueError(f"{name} must be a positive integer")
            values[complexity] = value
        return cls(values)

    def for_complexity(self, complexity: ComplexityLevel | str) -> int:
        normalized = (
            complexity
            if isinstance(complexity, ComplexityLevel)
            else ComplexityLevel(str(complexity))
        )
        return int(self.budgets[normalized])


__all__ = ["PlanningBudgetPolicy"]
