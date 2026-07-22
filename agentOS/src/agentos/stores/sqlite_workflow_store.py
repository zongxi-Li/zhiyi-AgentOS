"""AgentOS Core 的存储 sqlite_workflow_store 模块，管理任务和运行记录的持久化边界。"""


from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

from agentos.core.models.types import AgentTask, WorkflowRun, WorkflowStatus
from agentos.stores.workflow_store import WorkflowStore, WorkflowStorePage, paginate_items, status_value


class SQLiteWorkflowStore(WorkflowStore):
    """基于 SQLite 的本地持久化 WorkflowStore。"""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.busy_timeout_ms = int(os.getenv("AGENTOS_SQLITE_BUSY_TIMEOUT_MS", "5000"))
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
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT payload FROM runs WHERE run_id = ?", (run.run_id,)).fetchone()
            if row is not None:
                existing = WorkflowRun.model_validate(json.loads(row["payload"]))
                if _reject_terminal_overwrite(existing, run):
                    return
            conn.execute(
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
            conn.commit()

    def get_run(self, run_id: str) -> WorkflowRun:
        row = self._fetch_one("SELECT payload FROM runs WHERE run_id = ?", (run_id,))
        if row is None:
            raise KeyError(f"workflow run not found: {run_id}")
        return WorkflowRun.model_validate(json.loads(row["payload"]))

    def list_tasks(
        self,
        *,
        status: WorkflowStatus | str | None = None,
        domain: str | None = None,
        source: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> WorkflowStorePage[AgentTask]:
        expected_status = status_value(status)
        rows = self._fetch_all("SELECT payload FROM tasks")
        tasks = [
            task
            for task in (AgentTask.model_validate(json.loads(row["payload"])) for row in rows)
            if _matches_task(task, status=expected_status, domain=domain, source=source)
        ]
        tasks.sort(key=lambda task: (task.created_at, task.task_id), reverse=True)
        return paginate_items(tasks, page=page, page_size=page_size)

    def list_runs(
        self,
        *,
        status: WorkflowStatus | str | None = None,
        domain: str | None = None,
        workflow_id: str | None = None,
        source: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> WorkflowStorePage[WorkflowRun]:
        expected_status = status_value(status)
        rows = self._fetch_all("SELECT payload FROM runs")
        runs = [
            run
            for run in (WorkflowRun.model_validate(json.loads(row["payload"])) for row in rows)
            if _matches_run(
                run,
                status=expected_status,
                domain=domain,
                workflow_id=workflow_id,
                source=source,
            )
        ]
        runs.sort(key=lambda run: (run.created_at, run.run_id), reverse=True)
        return paginate_items(runs, page=page, page_size=page_size)

    def list_non_terminal_runs(self, *, limit: int = 200) -> tuple[WorkflowRun, ...]:
        safe_limit = max(1, limit)
        rows = self._fetch_all(
            """
            SELECT payload FROM runs
            WHERE json_extract(payload, '$.status') NOT IN (?, ?, ?)
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (
                WorkflowStatus.COMPLETED.value,
                WorkflowStatus.FAILED.value,
                WorkflowStatus.CANCELLED.value,
                safe_limit,
            ),
        )
        return tuple(
            WorkflowRun.model_validate(json.loads(row["payload"])) for row in rows
        )

    def find_run_by_idempotency_key(self, idempotency_key: str) -> WorkflowRun | None:
        row = self._fetch_one(
            """
            SELECT payload FROM runs
            WHERE json_extract(payload, '$.idempotencyKey') = ?
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (idempotency_key,),
        )
        if row is None:
            return None
        return WorkflowRun.model_validate(json.loads(row["payload"]))

    def _init_schema(self) -> None:
        with self._connect() as conn:
            journal_mode = conn.execute("PRAGMA journal_mode=WAL").fetchone()[0]
            if str(journal_mode).lower() != "wal":
                raise RuntimeError(f"SQLite WAL mode is required, got: {journal_mode}")
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
        with self._connect() as conn:
            conn.execute(sql, params)
            conn.commit()

    def _fetch_one(self, sql: str, params: tuple):
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(sql, params)
            return cursor.fetchone()

    def _fetch_all(self, sql: str, params: tuple = ()):
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(sql, params)
            return cursor.fetchall()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=max(self.busy_timeout_ms, 1) / 1000)
        conn.execute(f"PRAGMA busy_timeout={max(self.busy_timeout_ms, 1)}")
        conn.execute("PRAGMA synchronous=FULL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def checkpoint(self) -> tuple[int, int, int]:
        """Flush committed WAL pages before maintenance operations."""
        with self._connect() as conn:
            row = conn.execute("PRAGMA wal_checkpoint(FULL)").fetchone()
            return tuple(int(value) for value in row)

    def backup_to(self, destination: str | Path) -> dict[str, int | str]:
        """Create and verify a transactionally consistent SQLite backup."""
        target = Path(destination)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.resolve() == self.db_path.resolve():
            raise ValueError("backup destination must differ from source database")
        with self._connect() as source, sqlite3.connect(target) as dest:
            source.backup(dest)
            dest.commit()
        with sqlite3.connect(target) as verify:
            integrity = str(verify.execute("PRAGMA integrity_check").fetchone()[0])
            if integrity.lower() != "ok":
                raise RuntimeError(f"SQLite backup integrity check failed: {integrity}")
            task_count = int(verify.execute("SELECT COUNT(*) FROM tasks").fetchone()[0])
            run_count = int(verify.execute("SELECT COUNT(*) FROM runs").fetchone()[0])
        return {
            "source": str(self.db_path),
            "destination": str(target),
            "integrity": integrity,
            "taskCount": task_count,
            "runCount": run_count,
        }


def _matches_task(task: AgentTask, *, status: str | None, domain: str | None, source: str | None) -> bool:
    if status is not None and task.status.value != status:
        return False
    if domain is not None and task.domain != domain:
        return False
    if source is not None and task.input.get("source") != source:
        return False
    return True


def _matches_run(
    run: WorkflowRun,
    *,
    status: str | None,
    domain: str | None,
    workflow_id: str | None,
    source: str | None,
) -> bool:
    if status is not None and run.status.value != status:
        return False
    if domain is not None and run.domain != domain:
        return False
    if workflow_id is not None and run.workflow_id != workflow_id:
        return False
    if source is not None and run.input.get("source") != source:
        return False
    return True


def _reject_terminal_overwrite(existing: WorkflowRun, incoming: WorkflowRun) -> bool:
    terminal = {
        WorkflowStatus.COMPLETED,
        WorkflowStatus.FAILED,
        WorkflowStatus.CANCELLED,
    }
    if existing.status == WorkflowStatus.FAILED and incoming.status == WorkflowStatus.RETRYING:
        return False
    if existing.status in terminal and incoming.status != existing.status:
        return True
    return existing.status in terminal and incoming.updated_at < existing.updated_at
