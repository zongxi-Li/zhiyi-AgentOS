"""Registry for application LangGraph workflow implementations."""

from __future__ import annotations

from typing import Any, Callable


LangGraphRuntimeFactory = Callable[..., Any]


class LangGraphImplementationRegistry:
    """Maps AgentOS implementationId values to concrete LangGraph runtime classes."""

    def __init__(self):
        self._implementations: dict[str, LangGraphRuntimeFactory] = {}

    def register(self, implementation_id: str, factory: LangGraphRuntimeFactory) -> None:
        normalized = self._normalize(implementation_id)
        if not normalized:
            raise ValueError("LangGraph implementation_id is required")
        self._implementations[normalized] = factory

    def resolve(self, implementation_id: str) -> LangGraphRuntimeFactory:
        normalized = self._normalize(implementation_id)
        try:
            return self._implementations[normalized]
        except KeyError as exc:
            raise ValueError(f"Unsupported LangGraph implementation: {implementation_id}") from exc

    def create(self, implementation_id: str, **kwargs) -> Any:
        return self.resolve(implementation_id)(**kwargs)

    def registered_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._implementations))

    @staticmethod
    def _normalize(implementation_id: str) -> str:
        return (implementation_id or "").strip()


_default_registry: LangGraphImplementationRegistry | None = None


def build_default_langgraph_registry() -> LangGraphImplementationRegistry:
    registry = LangGraphImplementationRegistry()
    from app.graphs.contract_review import LegalContractReviewStateGraphRuntime

    registry.register(
        "legal_contract_review_stategraph_v1",
        LegalContractReviewStateGraphRuntime,
    )
    return registry


def get_default_langgraph_registry(*, refresh: bool = False) -> LangGraphImplementationRegistry:
    global _default_registry
    if refresh or _default_registry is None:
        _default_registry = build_default_langgraph_registry()
    return _default_registry
