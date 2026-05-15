from typing import Dict, Iterable, Optional

from core.skills.base import BaseSkill
from core.skills.builtin.case_retrieval_skill import CaseRetrievalSkill
from core.skills.builtin.case_understanding_skill import CaseUnderstandingSkill
from core.skills.builtin.document_generation_skill import DocumentGenerationSkill
from core.skills.builtin.evidence_analysis_skill import EvidenceAnalysisSkill
from core.skills.builtin.hearing_outline_generation_skill import HearingOutlineGenerationSkill
from core.skills.builtin.jurisdiction_determination_skill import JurisdictionDeterminationSkill
from core.skills.builtin.limitation_calculation_skill import LimitationCalculationSkill
from core.skills.builtin.programmer import (
    CodeGenerationSkill,
    CodebaseSemanticSearchSkill,
    DiagramGenerationSkill,
    RequirementAnalysisSkill,
)
from core.skills.builtin.risk_assessment_skill import RiskAssessmentSkill
from core.skills.builtin.statute_retrieval_skill import StatuteRetrievalSkill
from core.skills.builtin.teacher import (
    ClassroomInteractionDesignSkill,
    ErrorAnalysisQuestionPushSkill,
    HomeworkGradingSkill,
    LearningPathPlanningSkill,
    LessonPlanGenerationSkill,
    ParentCommunicationSuggestionSkill,
    ProgressReportGenerationSkill,
    StudentDiagnosisSkill,
    TutoringQASkill,
)
from core.skills.builtin.writer import (
    CharacterRelationSkill,
    ContentWriteSkill,
    InspirationExpandSkill,
    OutlineGenerateSkill,
)


class SkillRegistry:
    """Registry for resolving built-in skills by role and action name."""

    def __init__(self):
        self._skills_by_role: Dict[str, Dict[str, BaseSkill]] = {}

    def register_role(self, role: str, skills: Dict[str, BaseSkill]) -> None:
        normalized_role = self._normalize_role(role)
        self._skills_by_role[normalized_role] = dict(skills or {})

    def register(self, role: str, action: str, skill: BaseSkill) -> None:
        normalized_role = self._normalize_role(role)
        normalized_action = (action or "").strip()
        if not normalized_action:
            raise ValueError("action is required when registering a skill")
        self._skills_by_role.setdefault(normalized_role, {})[normalized_action] = skill

    def resolve(self, role: str, action: str) -> Optional[BaseSkill]:
        normalized_role = self._normalize_role(role, default="lawyer")
        normalized_action = (action or "").strip()
        role_skills = self._skills_by_role.get(normalized_role)
        if role_skills and normalized_action in role_skills:
            return role_skills[normalized_action]
        fallback_skills = self._skills_by_role.get("lawyer", {})
        return fallback_skills.get(normalized_action)

    def skills_for_role(self, role: str) -> Dict[str, BaseSkill]:
        normalized_role = self._normalize_role(role)
        return dict(self._skills_by_role.get(normalized_role, {}))

    def roles(self) -> Iterable[str]:
        return tuple(self._skills_by_role.keys())

    @staticmethod
    def _normalize_role(role: str, default: str = "") -> str:
        normalized = (role or default).strip().lower()
        if not normalized:
            raise ValueError("role is required when registering role-based skills")
        return normalized


def build_builtin_skill_registry(
    enabled_roles: Optional[Iterable[str]] = None,
    lawyer_skills: Optional[Dict[str, BaseSkill]] = None,
) -> SkillRegistry:
    registry = SkillRegistry()
    normalized_enabled = {
        (role or "").strip().lower()
        for role in (enabled_roles or ["lawyer", "teacher", "programmer", "writer"])
        if (role or "").strip()
    }

    if "lawyer" in normalized_enabled:
        registry.register_role("lawyer", lawyer_skills or _build_default_lawyer_skills())
    if "teacher" in normalized_enabled:
        registry.register_role("teacher", _build_default_teacher_skills())
    if "programmer" in normalized_enabled:
        registry.register_role("programmer", _build_default_programmer_skills())
    if "writer" in normalized_enabled:
        registry.register_role("writer", _build_default_writer_skills())
    return registry


def _build_default_lawyer_skills() -> Dict[str, BaseSkill]:
    return {
        "case_understanding": CaseUnderstandingSkill(),
        "statute_retrieval": StatuteRetrievalSkill(),
        "case_retrieval": CaseRetrievalSkill(),
        "evidence_analysis": EvidenceAnalysisSkill(),
        "limitation_calculation": LimitationCalculationSkill(),
        "jurisdiction_determination": JurisdictionDeterminationSkill(),
        "hearing_outline_generation": HearingOutlineGenerationSkill(),
        "document_generation": DocumentGenerationSkill(),
        "risk_assessment": RiskAssessmentSkill(),
    }


def _build_default_teacher_skills() -> Dict[str, BaseSkill]:
    return {
        "student_diagnosis": StudentDiagnosisSkill(),
        "lesson_plan_generation": LessonPlanGenerationSkill(),
        "homework_grading": HomeworkGradingSkill(),
        "error_analysis_question_push": ErrorAnalysisQuestionPushSkill(),
        "tutoring_qa": TutoringQASkill(),
        "learning_path_planning": LearningPathPlanningSkill(),
        "progress_report_generation": ProgressReportGenerationSkill(),
        "classroom_interaction_design": ClassroomInteractionDesignSkill(),
        "parent_communication_suggestion": ParentCommunicationSuggestionSkill(),
    }


def _build_default_programmer_skills() -> Dict[str, BaseSkill]:
    return {
        "requirement_analysis": RequirementAnalysisSkill(),
        "codebase_semantic_search": CodebaseSemanticSearchSkill(),
        "code_generation": CodeGenerationSkill(),
        "diagram_generation": DiagramGenerationSkill(),
    }


def _build_default_writer_skills() -> Dict[str, BaseSkill]:
    return {
        "inspiration_expand": InspirationExpandSkill(),
        "outline_generate": OutlineGenerateSkill(),
        "content_write": ContentWriteSkill(),
        "character_relation_map": CharacterRelationSkill(),
    }
