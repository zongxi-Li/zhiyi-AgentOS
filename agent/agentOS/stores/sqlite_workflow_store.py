from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

from agentos.core.types import AgentTask, WorkflowRun
from agentos.stores.workflow_store import WorkflowStore


class SQLiteWorkflowStore(WorkflowStore):
    """SQLite-backed WorkflowStore for durable local persistence."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def save_task(self, task: AgentTask) -> None:
        self._execute(
            """
            INSERT INTO tasks(task_id, payload, updated_at)
            VALUES(?, ?, ?)
            ON CONFLICT(task_id) DO UPDATE SET
                payload=excluded.payload,
                updated_at=excluded.updated_at
            """,
            (task.task_id, json.dumps(task.model_dump(by_alias=True, mode="json"), ensure_ascii=False), task.updated_at.isoformat()),
        )

    def get_task(self, task_id: str) -> AgentTask:
        row = self._fetch_one("SELECT payload FROM tasks WHERE task_id = ?", (task_id,))
        if row is None:
            raise KeyError(f"task not found: {task_id}")
        return AgentTask.model_validate(json.loads(row["payload"]))

    def save_run(self, run: WorkflowRun) -> None:
        self._execute(
            """
            INSERT INTO runs(run_id, task_id, payload, updated_at)
            VALUES(?, ?, ?, ?)
            ON CONFLICT(run_id) DO UPDATE SET
                task_id=excluded.task_id,
                payload=excluded.payload,
                updated_at=excluded.updated_at
            """,
            (
                run.run_id,
                run.task_id,
                json.dumps(run.model_dump(by_alias=True, mode="json"), ensure_ascii=False),
                run.updated_at.isoformat(),
            ),
        )

    def get_run(self, run_id: str) -> WorkflowRun:
        row = self._fetch_one("SELECT payload FROM runs WHERE run_id = ?", (run_id,))
        if row is None:
            raise KeyError(f"workflow run not found: {run_id}")
        return WorkflowRun.model_validate(json.loads(row["payload"]))

    def list_runs(self) -> Iterable[WorkflowRun]:
        rows = self._fetch_all("SELECT payload FROM runs ORDER BY updated_at ASC, run_id ASC")
        return tuple(WorkflowRun.model_validate(json.loads(row["payload"])) for row in rows)

    def _init_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def _execute(self, sql: str, params: tuple) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(sql, params)
            conn.commit()

    def _fetch_one(self, sql: str, params: tuple):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(sql, params)
            return cursor.fetchone()

    def _fetch_all(self, sql: str, params: tuple = ()):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(sql, params)
            return cursor.fetchall()
