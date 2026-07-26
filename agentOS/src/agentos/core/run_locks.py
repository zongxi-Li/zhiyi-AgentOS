"""Process-wide per-run locking for AgentOS runtime mutations.

The stage-one runtime graph MVP is explicitly single-process.  This manager
provides the one lock namespace shared by runtime controllers and lifecycle
operations inside that process.  It is not a distributed lock or a database
compare-and-set substitute.
"""

from __future__ import annotations

import asyncio
from threading import Lock


class RunLockManager:
    """Own one reusable ``asyncio.Lock`` for each workflow run id."""

    def __init__(self) -> None:
        self._locks: dict[str, asyncio.Lock] = {}
        self._registry_lock = Lock()

    def lock_for(self, run_id: str) -> asyncio.Lock:
        """Return the process-wide lock associated with ``run_id``."""

        normalized = str(run_id or "").strip()
        if not normalized:
            raise ValueError("run_id is required")
        with self._registry_lock:
            lock = self._locks.get(normalized)
            if lock is None:
                lock = asyncio.Lock()
                self._locks[normalized] = lock
            return lock


GLOBAL_RUN_LOCK_MANAGER = RunLockManager()


__all__ = ["RunLockManager", "GLOBAL_RUN_LOCK_MANAGER"]
