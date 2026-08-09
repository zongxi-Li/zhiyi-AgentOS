"""Bounded, auditable inputs for cognitive planning."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from typing import Any, Iterable

from agentos.core.planning.capabilities import CapabilityCatalog


PLANNING_MATERIAL_MAX_CHARS = 12_000
_HEAD_CHARS = 3_000
_TAIL_CHARS = 2_000
_WINDOW_RADIUS = 300
_FILL_CHUNK = 500


def _strings(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        values = [value]
    elif isinstance(value, set):
        values = sorted(value, key=str)
    elif isinstance(value, (list, tuple)):
        values = list(value)
    else:
        values = []
    return tuple(
        dict.fromkeys(
            str(item).strip()
            for item in values
            if item is not None and str(item).strip()
        )
    )


@dataclass(frozen=True)
class PlanningMaterialContext:
    excerpt: str = ""
    digest: str | None = None
    summary_digest: str | None = None
    total_characters: int = 0
    selected_characters: int = 0
    truncated: bool = False
    source_count: int = 0

    def to_diagnostics(self) -> dict[str, Any]:
        return {
            "included": bool(self.excerpt),
            "digest": self.digest,
            "materialDigest": self.digest,
            "summaryDigest": self.summary_digest,
            "totalCharacters": self.total_characters,
            "selectedCharacters": self.selected_characters,
            "truncated": self.truncated,
            "sourceCount": self.source_count,
        }


@dataclass(frozen=True)
class PlanningRequestContext:
    intent: str
    domain: str = "general"
    task_type: str = "general"
    constraints: tuple[str, ...] = ()
    expected_artifacts: tuple[str, ...] = ()
    verification_requirements: tuple[str, ...] = ()
    material: PlanningMaterialContext = field(default_factory=PlanningMaterialContext)

    @classmethod
    def from_task_input(
        cls,
        *,
        intent: str,
        domain: str,
        task_type: str,
        task_input: dict[str, Any],
        capability_catalog: CapabilityCatalog,
    ) -> "PlanningRequestContext":
        constraints = _strings(task_input.get("constraints"))
        expected_artifacts = _strings(task_input.get("expectedArtifacts"))
        verification_requirements = _strings(task_input.get("verificationRequirements"))
        materials = _strings(
            [task_input.get("materialText"), task_input.get("contractText")]
        )
        keywords = [*constraints, *expected_artifacts, *verification_requirements]
        for descriptor in capability_catalog.available(domain):
            keywords.extend(
                [descriptor.capability_id, descriptor.display_name, *descriptor.aliases]
            )
        material = build_material_context(materials, keywords=keywords)
        return cls(
            intent=str(intent or "").strip(),
            domain=str(domain or "general").strip() or "general",
            task_type=str(task_type or "general").strip() or "general",
            constraints=constraints,
            expected_artifacts=expected_artifacts,
            verification_requirements=verification_requirements,
            material=material,
        )

    @property
    def searchable_text(self) -> str:
        parts = [
            self.intent,
            *self.constraints,
            *self.expected_artifacts,
            *self.verification_requirements,
            self.material.excerpt,
        ]
        return "\n".join(item for item in parts if item)


def build_material_context(
    materials: Iterable[str],
    *,
    keywords: Iterable[str] = (),
    max_characters: int = PLANNING_MATERIAL_MAX_CHARS,
) -> PlanningMaterialContext:
    normalized = tuple(
        dict.fromkeys(
            str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()
            for value in materials
            if str(value or "").strip()
        )
    )
    if not normalized:
        return PlanningMaterialContext()
    full_text = "\n\n===== MATERIAL =====\n\n".join(normalized)
    digest = hashlib.sha256(full_text.encode("utf-8")).hexdigest()
    if len(full_text) <= max_characters:
        return PlanningMaterialContext(
            excerpt=full_text,
            digest=digest,
            summary_digest=digest,
            total_characters=len(full_text),
            selected_characters=len(full_text),
            source_count=len(normalized),
        )

    base_ranges: list[tuple[int, int]] = [
        (0, min(_HEAD_CHARS, len(full_text))),
        (max(0, len(full_text) - _TAIL_CHARS), len(full_text)),
    ]
    middle_ranges: list[tuple[int, int]] = []
    lowered = full_text.lower()
    terms = sorted(
        {
            str(term or "").strip().lower()
            for term in keywords
            if len("".join(str(term or "").split())) >= 2
        },
        key=lambda item: (-len(item), item),
    )
    # Direct source searches keep selection offsets stable and auditable.
    for term in terms:
        start = 0
        while True:
            position = lowered.find(term, start)
            if position < 0:
                break
            middle_ranges.append(
                (
                    max(_HEAD_CHARS, position - _WINDOW_RADIUS),
                    min(len(full_text) - _TAIL_CHARS, position + len(term) + _WINDOW_RADIUS),
                )
            )
            start = position + max(1, len(term))
    # Reserve room for at most thirteen visible omission separators.
    middle_limit = max(0, max_characters - _HEAD_CHARS - _TAIL_CHARS - 48)
    middle_ranges = _fit_ranges(
        middle_ranges,
        limit=middle_limit,
        text_length=len(full_text),
    )
    selected = _ranges_length(middle_ranges)
    middle_start = _HEAD_CHARS
    middle_end = max(middle_start, len(full_text) - _TAIL_CHARS)
    cursor = middle_start
    while selected < max_characters and cursor < middle_end:
        remaining = max_characters - selected
        width = min(_FILL_CHUNK, remaining, middle_end - cursor)
        middle_ranges = _fit_ranges(
            [*middle_ranges, (cursor, cursor + width)],
            limit=middle_limit,
            text_length=len(full_text),
        )
        selected = _ranges_length(middle_ranges)
        cursor += max(_FILL_CHUNK, (middle_end - middle_start) // 12 or _FILL_CHUNK)

    ranges = _fit_ranges(
        [*base_ranges, *middle_ranges],
        limit=max_characters,
        text_length=len(full_text),
    )
    chunks = [full_text[start:end] for start, end in ranges if end > start]
    excerpt = "\n…\n".join(chunks)
    if len(excerpt) > max_characters:
        excerpt = excerpt[:max_characters]
    return PlanningMaterialContext(
        excerpt=excerpt,
        digest=digest,
        summary_digest=hashlib.sha256(excerpt.encode("utf-8")).hexdigest(),
        total_characters=len(full_text),
        selected_characters=len(excerpt),
        truncated=True,
        source_count=len(normalized),
    )


def _fit_ranges(
    ranges: Iterable[tuple[int, int]],
    *,
    limit: int,
    text_length: int,
) -> list[tuple[int, int]]:
    merged: list[list[int]] = []
    for raw_start, raw_end in sorted(ranges):
        start = max(0, min(text_length, raw_start))
        end = max(start, min(text_length, raw_end))
        if end <= start:
            continue
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    fitted: list[tuple[int, int]] = []
    remaining = limit
    for start, end in merged:
        if remaining <= 0 or len(fitted) >= 14:
            break
        end = min(end, start + remaining)
        fitted.append((start, end))
        remaining -= end - start
    return fitted


def _ranges_length(ranges: Iterable[tuple[int, int]]) -> int:
    return sum(max(0, end - start) for start, end in ranges)


__all__ = [
    "PLANNING_MATERIAL_MAX_CHARS",
    "PlanningMaterialContext",
    "PlanningRequestContext",
    "build_material_context",
]
