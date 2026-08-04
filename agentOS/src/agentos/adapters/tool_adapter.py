"""Application-neutral tool runtime registration for AgentOS."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Protocol


class ToolRuntime(Protocol):
    def scoped(self, allowed_tools: Iterable[str]) -> "ToolRuntime": ...

    async def run(self, text: str, **kwargs: Any) -> Any: ...

    async def execute(self, name: str, arguments: dict[str, Any], **kwargs: Any) -> Any: ...


DEFAULT_ACG_TOOL_TIMEOUT_SECONDS = 20.0


def network_tools_enabled(task_input: dict[str, Any] | None) -> bool:
    """Return the ACG network policy, defaulting to enabled with an explicit opt-out."""

    value = (task_input or {}).get("webSearchEnabled", True)
    if isinstance(value, str):
        return value.strip().lower() not in {"0", "false", "off", "disabled", "no"}
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value != 0
    return value is not False


@dataclass(frozen=True)
class BoundedToolRuntime:
    """Apply an outer deadline to an application-provided tool runtime.

    The production tool runtime already bounds individual provider calls.  This
    adapter is a second guard at the Core boundary so a faulty or custom runtime
    cannot leave an ACG node waiting forever.
    """

    delegate: ToolRuntime
    timeout_seconds: float = DEFAULT_ACG_TOOL_TIMEOUT_SECONDS

    def scoped(self, allowed_tools: Iterable[str]) -> "BoundedToolRuntime":
        return BoundedToolRuntime(
            self.delegate.scoped(allowed_tools),
            timeout_seconds=self.timeout_seconds,
        )

    async def run(self, text: str, **kwargs: Any) -> Any:
        return await self._wait(self.delegate.run(text, **kwargs))

    async def execute(self, name: str, arguments: dict[str, Any], **kwargs: Any) -> Any:
        return await self._wait(self.delegate.execute(name, arguments, **kwargs))

    async def _wait(self, awaitable) -> Any:
        return await asyncio.wait_for(
            awaitable,
            timeout=max(0.01, float(self.timeout_seconds)),
        )


ToolRuntimeFactory = Callable[[], ToolRuntime]
_tool_runtime_factory: ToolRuntimeFactory | None = None


def register_tool_runtime_factory(factory: ToolRuntimeFactory) -> None:
    global _tool_runtime_factory
    _tool_runtime_factory = factory


def clear_tool_runtime_factory() -> None:
    global _tool_runtime_factory
    _tool_runtime_factory = None


def configured_tool_runtime() -> ToolRuntime | None:
    return _tool_runtime_factory() if _tool_runtime_factory is not None else None


__all__ = [
    "BoundedToolRuntime",
    "DEFAULT_ACG_TOOL_TIMEOUT_SECONDS",
    "ToolRuntime",
    "ToolRuntimeFactory",
    "clear_tool_runtime_factory",
    "configured_tool_runtime",
    "network_tools_enabled",
    "register_tool_runtime_factory",
]
