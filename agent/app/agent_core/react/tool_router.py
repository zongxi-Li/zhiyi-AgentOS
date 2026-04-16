import importlib
import logging
from typing import Dict, Optional

from app.agent_core.schema.agent_types import PlannedAction, SkillRequest, SkillResult
from app.agent_core.skills.base import BaseSkill, NoOpSkill
from app.agent_core.skills.case_retrieval_skill import CaseRetrievalSkill
from app.agent_core.skills.case_understanding_skill import CaseUnderstandingSkill
from app.agent_core.skills.document_generation_skill import DocumentGenerationSkill
from app.agent_core.skills.evidence_analysis_skill import EvidenceAnalysisSkill
from app.agent_core.skills.hearing_outline_generation_skill import HearingOutlineGenerationSkill
from app.agent_core.skills.jurisdiction_determination_skill import JurisdictionDeterminationSkill
from app.agent_core.skills.limitation_calculation_skill import LimitationCalculationSkill
from app.agent_core.skills.risk_assessment_skill import RiskAssessmentSkill
from app.agent_core.skills.statute_retrieval_skill import StatuteRetrievalSkill

logger = logging.getLogger(__name__)


class ToolRouter:
    """Routes planned actions to concrete skills by role."""

    TEACHER_SKILL_SPECS = {
        "student_diagnosis": "app.agent_core.skills.teacher.student_diagnosis_skill:StudentDiagnosisSkill",
        "lesson_plan_generation": "app.agent_core.skills.teacher.lesson_plan_generation_skill:LessonPlanGenerationSkill",
        "homework_grading": "app.agent_core.skills.teacher.homework_grading_skill:HomeworkGradingSkill",
        "error_analysis_question_push": "app.agent_core.skills.teacher.error_analysis_question_push_skill:ErrorAnalysisQuestionPushSkill",
        "tutoring_qa": "app.agent_core.skills.teacher.tutoring_qa_skill:TutoringQASkill",
        "learning_path_planning": "app.agent_core.skills.teacher.learning_path_planning_skill:LearningPathPlanningSkill",
        "progress_report_generation": "app.agent_core.skills.teacher.progress_report_generation_skill:ProgressReportGenerationSkill",
        "classroom_interaction_design": "app.agent_core.skills.teacher.classroom_interaction_design_skill:ClassroomInteractionDesignSkill",
        "parent_communication_suggestion": "app.agent_core.skills.teacher.parent_communication_suggestion_skill:ParentCommunicationSuggestionSkill",
    }

    def __init__(self, skills: Optional[Dict[str, BaseSkill]] = None):
        self.skills_by_role: Dict[str, Dict[str, BaseSkill]] = {}

        self.register_skills_for_role("lawyer", skills or self._build_default_lawyer_skills())
        self.register_skills_for_role("teacher", self._build_default_teacher_skills())

    def _build_default_lawyer_skills(self) -> Dict[str, BaseSkill]:
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

    def _load_teacher_skill(self, action_name: str, spec: str) -> BaseSkill:
        module_name, class_name = spec.split(":", maxsplit=1)
        try:
            module = importlib.import_module(module_name)
            skill_cls = getattr(module, class_name)
            skill = skill_cls()
            if isinstance(skill, BaseSkill):
                return skill
            logger.warning("Loaded teacher skill for %s is not a BaseSkill, using NoOp.", action_name)
        except Exception as exc:
            logger.info("Teacher skill %s not ready yet, using NoOp placeholder. error=%s", action_name, exc)
        return NoOpSkill(action_name)

    def _build_default_teacher_skills(self) -> Dict[str, BaseSkill]:
        skills: Dict[str, BaseSkill] = {}
        for action_name, spec in self.TEACHER_SKILL_SPECS.items():
            skills[action_name] = self._load_teacher_skill(action_name, spec)
        return skills

    def register_skills_for_role(self, role: str, skills: Dict[str, BaseSkill]) -> None:
        normalized_role = (role or "").strip().lower()
        if not normalized_role:
            raise ValueError("role is required when registering role-based skills")
        self.skills_by_role[normalized_role] = dict(skills or {})

    async def run(self, action: PlannedAction, request: SkillRequest, role: str = "lawyer") -> SkillResult:
        normalized_role = (role or "lawyer").strip().lower()
        skills = self.skills_by_role.get(normalized_role)
        if skills is None:
            skills = self.skills_by_role.get("lawyer", {})

        skill = skills.get(action.action, NoOpSkill(action.action))
        return await skill.run(request)
