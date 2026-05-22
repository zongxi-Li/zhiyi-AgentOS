"""AgentOS Core 的存储 sqlite_workflow_store 模块，管理任务和运行记录的持久化边界。"""


from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from agentos.core.models.types import AgentTask, WorkflowRun, WorkflowStatus
from agentos.stores.workflow_store import WorkflowStore, WorkflowStorePage, paginate_items, status_value


class SQLiteWorkflowStore(WorkflowStore):
    """基于 SQLite 的本地持久化 WorkflowStore。"""

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
