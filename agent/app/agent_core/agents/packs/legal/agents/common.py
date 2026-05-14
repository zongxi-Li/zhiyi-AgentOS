from typing import Any, Dict, List


def case_text(task_input: Dict[str, Any]) -> str:
    return str(
        task_input.get("caseText")
        or task_input.get("contractText")
        or task_input.get("text")
        or ""
    ).strip()


def has_any(text: str, tokens: List[str]) -> bool:
    raw = text or ""
    lowered = raw.lower()
    return any(token in raw for token in tokens) or any(token in lowered for token in tokens)


def dedupe(items: List[str]) -> List[str]:
    seen = set()
    result = []
    for item in items:
        normalized = str(item).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result
