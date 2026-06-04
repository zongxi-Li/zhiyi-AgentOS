"""AgentOS TUI main application entry point.

ZhiYi AgentOS Terminal Workbench -- a Textual TUI for interacting with the
AgentOS multi-agent workflow platform.
"""

from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from textual.app import App, Binding
from textual.reactive import reactive

from kinlin_tui.api.client import AgentOSClient
from kinlin_tui.screens.chat import ChatScreen
from kinlin_tui.screens.dashboard import DashboardScreen
from kinlin_tui.theme import (
    RoleTheme,
    TEXTUAL_THEME_CSS,
)


class AgentOSTuiApp(App):
    """Textual application for the AgentOS terminal workbench."""

    # ---- Textual metadata ---------------------------------------------------

    CSS = TEXTUAL_THEME_CSS

    SCREENS = {
        "chat": ChatScreen,
        "dashboard": DashboardScreen,
    }

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
    ]

    # ---- Reactive state ----------------------------------------------------

    current_role: RoleTheme = reactive(RoleTheme.LAWYER)
    api_client: AgentOSClient
    _managed_backend: subprocess.Popen[bytes] | None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def __init__(self, managed_backend: subprocess.Popen[bytes] | None = None) -> None:
        super().__init__()
        self._managed_backend = managed_backend
        api_url = os.environ.get("AGENTOS_API_URL", "http://127.0.0.1:8000/ai")
        self.api_client = AgentOSClient(base_url=api_url)

    async def on_mount(self) -> None:
        """Push the initial chat screen and configure its header."""
        await self.push_screen("chat")
        screen = self.screen
        try:
            header = screen.query_one("#header")
            header.role = self.current_role
            header.cwd = os.path.basename(os.getcwd())
        except Exception:
            pass

    async def on_current_role_changed(self, value: RoleTheme) -> None:
        """Propagate role changes to the active screen's header."""
        screen = self.screen
        try:
            header = screen.query_one("#header")
            header.role = value
        except Exception:
            return

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    def action_switch_screen(self, name: str) -> None:
        """Push to the named screen, or pop back to it if already on the stack.

        Args:
            name: A key from ``SCREENS``, e.g. ``"chat"`` or ``"dashboard"``.
        """
        if name not in self.SCREENS:
            return

        target_cls = self.SCREENS[name]
        stack = list(self.screen_stack)

        # Walk the stack bottom-up to find an existing instance of the target.
        for idx, s in enumerate(stack):
            if isinstance(s, target_cls):
                # Pop back until that screen is on top.
                pops_needed = len(stack) - idx - 1
                for _ in range(pops_needed):
                    self.pop_screen()
                return

        # Not on the stack -- push a fresh instance.
        self.push_screen(name)

    # Convenience alias so screen code can call app.switch_screen(name).
    switch_screen = action_switch_screen

    # ------------------------------------------------------------------
    # Teardown
    # ------------------------------------------------------------------

    async def on_unmount(self) -> None:
        """Close the API client when the app exits."""
        await self.api_client.close()
        _stop_managed_backend(self._managed_backend)


# ============================================================================
# CLI entry point
# ============================================================================


def _service_root_from_api_url(api_url: str) -> str:
    """Return the service root URL for an AgentOS API base URL."""
    root = api_url.rstrip("/")
    if root.endswith("/ai"):
        root = root[:-3]
    return root.rstrip("/")


def _api_health_ok(api_url: str, timeout: float = 2.0) -> bool:
    """Check the backend health endpoint without raising on network errors."""
    url = f"{_service_root_from_api_url(api_url)}/health"
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return 200 <= response.status < 300
    except (OSError, urllib.error.URLError, urllib.error.HTTPError):
        return False


def _port_available(port: int) -> bool:
    """Return True when localhost can bind to *port*."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def _find_available_port(preferred: int) -> int:
    """Find an available local backend port near *preferred*."""
    candidates = list(range(preferred, preferred + 50)) + list(range(8765, 8790))
    seen: set[int] = set()
    for port in candidates:
        if port in seen:
            continue
        seen.add(port)
        if _port_available(port):
            return port
    raise RuntimeError("No free local port found for the AgentOS backend.")


def _repo_root() -> Path | None:
    """Locate the repository root that contains the Python AI service."""
    candidates = [Path.cwd(), *Path(__file__).resolve().parents]
    for candidate in candidates:
        if (candidate / "agent" / "app" / "main.py").exists():
            return candidate
    return None


def _start_local_backend(port: int) -> subprocess.Popen[bytes]:
    """Start the local FastAPI backend on *port*."""
    root = _repo_root()
    if root is None:
        raise RuntimeError("Cannot locate repository root with agent/app/main.py.")

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return subprocess.Popen(
        [
            sys.executable,
            "-X",
            "utf8",
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=root / "agent",
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creationflags,
    )


def _stop_managed_backend(process: subprocess.Popen[bytes] | None) -> None:
    """Stop a backend process started by this CLI."""
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()


def _ensure_default_local_api() -> subprocess.Popen[bytes] | None:
    """Ensure a usable local backend when no explicit API URL was provided."""
    default_api_url = "http://127.0.0.1:8000/ai"
    if _api_health_ok(default_api_url):
        return None

    port = _find_available_port(8000)
    api_url = f"http://127.0.0.1:{port}/ai"
    print(f"Starting local AgentOS backend on {api_url} ...", flush=True)
    process = _start_local_backend(port)

    for _ in range(240):
        if process.poll() is not None:
            raise RuntimeError("Local AgentOS backend exited before becoming healthy.")
        if _api_health_ok(api_url):
            os.environ["AGENTOS_API_URL"] = api_url
            print("AgentOS backend is ready.", flush=True)
            return process
        time.sleep(0.5)

    _stop_managed_backend(process)
    raise RuntimeError("Timed out waiting for local AgentOS backend health check.")


def _run_os(args: argparse.Namespace) -> None:
    """Launch the AgentOS TUI."""
    managed_backend: subprocess.Popen[bytes] | None = None
    if args.api_url:
        os.environ["AGENTOS_API_URL"] = args.api_url
    elif "AGENTOS_API_URL" not in os.environ:
        managed_backend = _ensure_default_local_api()

    role_map: dict[str, RoleTheme] = {
        "lawyer": RoleTheme.LAWYER,
        "teacher": RoleTheme.TEACHER,
        "programmer": RoleTheme.PROGRAMMER,
        "writer": RoleTheme.WRITER,
    }

    app = AgentOSTuiApp(managed_backend=managed_backend)
    app.current_role = role_map.get(args.role, RoleTheme.LAWYER)
    app.run()


def _run_start(args: argparse.Namespace) -> None:
    """Start Docker services then launch TUI."""
    import subprocess
    import time

    print("Starting Docker services...")
    subprocess.run(["docker", "compose", "up", "-d", "ai-service"], check=True)

    url = f"http://127.0.0.1:8000/health"
    print("Waiting for ai-service...", end="", flush=True)
    for _ in range(30):
        try:
            import urllib.request
            urllib.request.urlopen(url, timeout=2)
            print(" OK")
            break
        except Exception:
            print(".", end="", flush=True)
            time.sleep(2)
    else:
        print(" TIMEOUT")
        sys.exit(1)

    os.environ["AGENTOS_API_URL"] = args.api_url or "http://127.0.0.1:8000/ai"
    role_map = {
        "lawyer": RoleTheme.LAWYER,
        "teacher": RoleTheme.TEACHER,
        "programmer": RoleTheme.PROGRAMMER,
        "writer": RoleTheme.WRITER,
    }
    app = AgentOSTuiApp()
    app.current_role = role_map.get(args.role, RoleTheme.LAWYER)
    app.run()


def _build_parser() -> argparse.ArgumentParser:
    """Build the ``zhiyi`` command parser."""
    parser = argparse.ArgumentParser(
        prog="zhiyi",
        description="ZhiYi AgentOS CLI",
    )
    sub = parser.add_subparsers(dest="command", title="commands")

    # ---- zhiyi os ----
    os_parser = sub.add_parser("os", help="Launch the AgentOS terminal workbench")
    os_parser.add_argument(
        "--role", "-r",
        default="lawyer",
        choices=["lawyer", "teacher", "programmer", "writer"],
        help="Agent role (default: lawyer)",
    )
    os_parser.add_argument(
        "--api-url",
        default=None,
        help="AgentOS API base URL (env: AGENTOS_API_URL)",
    )
    os_parser.set_defaults(func=_run_os)

    # ---- zhiyi start ----
    start_parser = sub.add_parser("start", help="Start Docker + launch TUI")
    start_parser.add_argument(
        "--role", "-r",
        default="lawyer",
        choices=["lawyer", "teacher", "programmer", "writer"],
    )
    start_parser.add_argument("--api-url", default=None)
    start_parser.set_defaults(func=_run_start)

    return parser


def _normalize_argv(argv: list[str]) -> list[str]:
    """Support the historical ``zhiyi --role lawyer`` launch form."""
    if argv and argv[0].startswith("-") and argv[0] not in {"-h", "--help"}:
        return ["os", *argv]
    return argv


def _parse_args(
    argv: list[str] | None = None,
) -> tuple[argparse.ArgumentParser, argparse.Namespace]:
    parser = _build_parser()
    raw_argv = sys.argv[1:] if argv is None else argv
    args = parser.parse_args(_normalize_argv(list(raw_argv)))
    return parser, args


def main(argv: list[str] | None = None) -> None:
    """zhiyi -- ZhiYi AgentOS CLI."""
    parser, args = _parse_args(argv)

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
