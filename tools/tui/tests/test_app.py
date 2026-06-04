"""Regression tests for the TUI app shell and chat screen."""

from __future__ import annotations

import asyncio

from textual.widgets import DataTable, Input, RichLog

from kinlin_tui.app import AgentOSTuiApp, _parse_args


class FakeClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    async def agent_chat(
        self,
        role: str,
        text: str,
        session_id: str | None = None,
    ) -> dict[str, str]:
        self.calls.append((role, text, session_id))
        return {"answer": "pong", "sessionId": "session-1"}

    async def close(self) -> None:
        pass


class DashboardClient(FakeClient):
    async def list_workflow_runs(self) -> dict:
        return {
            "items": [
                {
                    "runId": "run_one",
                    "workflowId": "legal_case_analysis_v1",
                    "domain": "legal",
                    "status": "completed",
                    "steps": [{"status": "completed"}],
                },
                {
                    "runId": "run_two",
                    "workflowId": "legal_case_analysis_v1",
                    "domain": "legal",
                    "status": "completed",
                    "steps": [{"status": "completed"}],
                },
            ]
        }


def test_bare_role_args_default_to_os_command() -> None:
    _parser, args = _parse_args(["--role", "teacher"])

    assert args.command == "os"
    assert args.role == "teacher"


def test_chat_submit_calls_agent_and_renders_reply() -> None:
    async def scenario() -> None:
        app = AgentOSTuiApp()
        await app.api_client.close()

        fake_client = FakeClient()
        app.api_client = fake_client  # type: ignore[assignment]

        async with app.run_test(size=(100, 30)) as pilot:
            input_widget = app.screen.query_one("#chat-input", Input)
            input_widget.value = "hello"

            await pilot.press("enter")
            await pilot.pause(0.1)

            log = app.screen.query_one("#message-log", RichLog)
            rendered_text = "\n".join(line.text for line in log.lines)

        assert fake_client.calls == [("lawyer", "hello", None)]
        assert "You: hello" in rendered_text
        assert "ZhiYi:" in rendered_text
        assert "pong" in rendered_text

    asyncio.run(scenario())


def test_chat_reuses_returned_session_id() -> None:
    async def scenario() -> None:
        app = AgentOSTuiApp()
        await app.api_client.close()

        fake_client = FakeClient()
        app.api_client = fake_client  # type: ignore[assignment]

        async with app.run_test(size=(100, 30)) as pilot:
            input_widget = app.screen.query_one("#chat-input", Input)
            input_widget.value = "first"
            await pilot.press("enter")
            await pilot.pause(0.1)

            input_widget = app.screen.query_one("#chat-input", Input)
            input_widget.value = "second"
            await pilot.press("enter")
            await pilot.pause(0.1)

        assert fake_client.calls == [
            ("lawyer", "first", None),
            ("lawyer", "second", "session-1"),
        ]

    asyncio.run(scenario())


def test_dashboard_accepts_camel_case_run_ids() -> None:
    async def scenario() -> None:
        app = AgentOSTuiApp()
        await app.api_client.close()

        app.api_client = DashboardClient()  # type: ignore[assignment]

        async with app.run_test(size=(100, 30)) as pilot:
            await app.push_screen("dashboard")
            await pilot.pause(0.2)

            table = app.screen.query_one("#runs-table", DataTable)
            assert table.row_count == 2

    asyncio.run(scenario())
