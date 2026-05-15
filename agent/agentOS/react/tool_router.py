from typing import Dict, List, Optional

from agentos.skills.base import BaseSkill, NoOpSkill
from agentos.skills.registry import SkillRegistry, build_builtin_skill_registry
from agentos.core.types import PlannedAction, SkillRequest, SkillResult


class ToolRouter:
    """Routes planned actions to concrete skills through SkillRegistry."""

    def __init__(
        self,
        skills: Optional[Dict[str, BaseSkill]] = None,
        enabled_roles: Optional[List[str]] = None,
        registry: Optional[SkillRegistry] = None,
    ):
        self.registry = registry or build_builtin_skill_registry(
            enabled_roles=enabled_roles,
            lawyer_skills=skills,
        )
        self.skills_by_role: Dict[str, Dict[str, BaseSkill]] = {
            role: self.registry.skills_for_role(role)
            for role in self.registry.roles()
        }

    def register_skills_for_role(self, role: str, skills: Dict[str, BaseSkill]) -> None:
        self.registry.register_role(role, skills)
        normalized_role = (role or "").strip().lower()
        self.skills_by_role[normalized_role] = dict(skills or {})

    async def run(self, action: PlannedAction, request: SkillRequest, role: str = "lawyer") -> SkillResult:
        skill = self.registry.resolve(role=role, action=action.action)
        if skill is None:
            skill = NoOpSkill(action.action)
        return await skill.run(request)
