from __future__ import annotations

from abc import ABC, abstractmethod

from agentos.core.types import SkillRequest, SkillResult


class BaseSkill(ABC):
    """Unified Interface for reusable skills."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def run(self, request: SkillRequest) -> SkillResult:
        raise NotImplementedError


class NoOpSkill(BaseSkill):
    """Fallback Skill used by tests and empty registries."""

    def __init__(self, name: str = "noop"):
        super().__init__(name)

    async def run(self, request: SkillRequest) -> SkillResult:
        return SkillResult(
            skillName=self.name,
            success=True,
            output={
                "text": request.text,
                "action_input": request.action_input,
            },
            message="NoOpSkill completed.",
        )
