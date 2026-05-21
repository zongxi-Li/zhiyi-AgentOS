"""Compatibility module for lowercase ``agentos`` imports.

The application layer can be launched with ``agent/`` as the first import
root. In that mode this module is discovered before the real package under
``agentOS/src``. Expose the real package path so existing ``import agentos``
callers continue to resolve AgentOS Core from the runtime package.
"""

from pathlib import Path

__path__ = [str(Path(__file__).resolve().parents[1] / "agentOS" / "src" / "agentos")]
