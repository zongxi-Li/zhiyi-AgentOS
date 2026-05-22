"""工作流注册表，负责保存、加载和推荐行业 Pack 提供的工作流定义。"""
# TODO 后期需要拓展为加载动态生成的拓扑图和工作流

import json
from pathlib import Path
from typing import Dict, Iterable, Optional

from agentos.core.models.types import WorkflowDefinition


class WorkflowRegistry:
    """保存并推荐行业 Pack 提供的工作流定义。"""

    """初始化类的设计"""
    def __init__(self):
        self._workflows: Dict[str, WorkflowDefinition] = {}

    def register(self, workflow: WorkflowDefinition) -> None:
        if not workflow.workflow_id:
            raise ValueError("workflow_id is required")
        if not workflow.steps:
            raise ValueError(f"workflow {workflow.workflow_id} must define at least one step")
        self._workflows[workflow.workflow_id] = workflow

    def get(self, workflow_id: str) -> WorkflowDefinition:
        try:
            return self._workflows[workflow_id]
        except KeyError as exc:
            raise KeyError(f"workflow not registered: {workflow_id}") from exc

    def all(self) -> tuple[str, ...]:
        return tuple(self._workflows.values())

    def recommend(self, domain: str, intent: str) -> Optional[WorkflowDefinition]:
        normalized_domain = (domain or "").strip().lower()
        normalized_intent = (intent or "").strip().lower()

        for workflow in self._workflows.values():
            if workflow.domain.lower() == normalized_domain and workflow.intent.lower() == normalized_intent:
                return workflow

        for workflow in self._workflows.values():
            if workflow.domain.lower() == normalized_domain:
                return workflow
        return None

    def load_file(self, path: Path) -> WorkflowDefinition:
        text = path.read_text(encoding="utf-8")
        try:
            import yaml  # type: ignore

            data = yaml.safe_load(text)
        except ModuleNotFoundError:
            data = json.loads(text)
        workflow = WorkflowDefinition.model_validate(data)
        self.register(workflow)
        return workflow

    def load_directory(self, directory: Path) -> None:
        if not directory.exists():
            return
        for path in sorted(directory.glob("*.yaml")):
            self.load_file(path)
