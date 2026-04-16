from typing import Dict, List, Optional

from app.agent_core.schema.agent_types import PlannedAction


class ReactPlanner:
    """Intent-aware ReAct planner for multi-role agent workflows."""

    def __init__(self, max_plan_steps: int = 10):
        self.max_plan_steps = max_plan_steps

    def _contains_any(self, text: str, tokens: List[str]) -> bool:
        raw = text or ""
        lowered = raw.lower()
        return any(token in raw for token in tokens) or any(token in lowered for token in tokens)

    def _slice_plan(self, actions: List[PlannedAction]) -> List[PlannedAction]:
        return actions[: self.max_plan_steps]

    def _infer_subject(self, text: str) -> str:
        if self._contains_any(text, ["math", "mathematics", "数学", "代数", "几何", "勾股"]):
            return "junior_math"
        if self._contains_any(text, ["physics", "物理", "力学", "电学", "压强", "运动"]):
            return "junior_physics"
        return "general"

    def _infer_grade(self, text: str) -> str:
        lowered = (text or "").lower()
        if "初一" in text or "七年级" in text or "grade 7" in lowered:
            return "grade_7"
        if "初二" in text or "八年级" in text or "grade 8" in lowered:
            return "grade_8"
        if "初三" in text or "九年级" in text or "grade 9" in lowered:
            return "grade_9"
        return "unknown"

    def _latest_user_text(self, history: List[Dict[str, str]]) -> str:
        for item in reversed(history or []):
            if item.get("role") == "user":
                return item.get("content", "")
        return ""

    def _is_teacher_follow_up(self, text: str, history: List[Dict[str, str]]) -> bool:
        if not (text or "").strip() or not history:
            return False

        follow_up_tokens = [
            "再",
            "继续",
            "补充",
            "优化",
            "改",
            "修改",
            "改成",
            "调整",
            "上一个",
            "刚才",
            "环节",
            "有趣",
            "that part",
            "part",
            "revise",
            "update",
            "refine",
            "make it",
            "improve",
        ]
        short_query = len((text or "").strip()) <= 80
        return short_query and self._contains_any(text, follow_up_tokens)

    def _resolve_teacher_follow_up_action(self, text: str, history: List[Dict[str, str]]) -> Optional[str]:
        probe_text = f"{text}\n{self._latest_user_text(history)}"

        if self._contains_any(probe_text, ["教案", "备课", "导入", "环节", "课堂流程", "lesson plan", "warm-up"]):
            return "lesson_plan_generation"
        if self._contains_any(probe_text, ["互动", "提问", "活动", "分组", "互动设计", "interaction", "activity"]):
            return "classroom_interaction_design"
        if self._contains_any(probe_text, ["批改", "评分", "评语", "作文", "grading", "rubric"]):
            return "homework_grading"
        if self._contains_any(probe_text, ["错题", "推题", "变式", "归因", "error analysis", "similar questions"]):
            return "error_analysis_question_push"
        if self._contains_any(probe_text, ["路径", "计划", "周计划", "learning plan", "roadmap"]):
            return "learning_path_planning"
        if self._contains_any(probe_text, ["报告", "学情报告", "report", "progress"]):
            return "progress_report_generation"
        if self._contains_any(probe_text, ["家长", "沟通", "parent", "guardian"]):
            return "parent_communication_suggestion"
        if self._contains_any(probe_text, ["答疑", "讲解", "不会", "question", "how to solve"]):
            return "tutoring_qa"
        return None

    def plan(self, text: str, history: List[Dict[str, str]], role: str = "lawyer") -> List[PlannedAction]:
        normalized_role = (role or "lawyer").strip().lower()
        if normalized_role == "teacher":
            return self.plan_teacher(text=text, history=history)
        return self.plan_lawyer(text=text, history=history)

    def plan_lawyer(self, text: str, history: List[Dict[str, str]]) -> List[PlannedAction]:
        actions: List[PlannedAction] = []
        added = set()

        def add_action(thought: str, action: str, action_input: Dict[str, object]) -> None:
            if action in added:
                return
            added.add(action)
            actions.append(
                PlannedAction(
                    thought=thought,
                    action=action,
                    actionInput=action_input,
                )
            )

        evidence_tokens = ["证据", "微信", "转账", "录音", "证人", "举证", "evidence", "proof"]
        limitation_tokens = ["时效", "过期", "截止", "诉讼时效", "limitation", "deadline"]
        jurisdiction_tokens = ["管辖", "哪个法院", "哪里起诉", "法院", "jurisdiction", "court"]
        hearing_tokens = ["开庭", "庭审", "提纲", "发问", "质证", "辩论", "hearing", "trial"]
        drafting_tokens = ["文书", "起诉状", "答辩状", "律师函", "草稿", "draft", "template"]

        needs_evidence = self._contains_any(text, evidence_tokens)
        needs_limitation = self._contains_any(text, limitation_tokens)
        needs_jurisdiction = self._contains_any(text, jurisdiction_tokens)
        needs_hearing = self._contains_any(text, hearing_tokens)
        needs_document = self._contains_any(text, drafting_tokens)

        add_action(
            thought="Structure the case facts and legal issues first.",
            action="case_understanding",
            action_input={"historySize": len(history)},
        )
        add_action(
            thought="Retrieve relevant statutes for legal grounding.",
            action="statute_retrieval",
            action_input={"query": text, "top_k": 5},
        )
        add_action(
            thought="Retrieve similar cases to support legal reasoning.",
            action="case_retrieval",
            action_input={"query": text, "top_k": 5},
        )

        if needs_evidence or needs_hearing:
            add_action(
                thought="Analyze available evidence and gaps.",
                action="evidence_analysis",
                action_input={"query": text},
            )
        if needs_limitation:
            add_action(
                thought="Calculate limitation period and deadline risks.",
                action="limitation_calculation",
                action_input={"query": text},
            )
        if needs_jurisdiction:
            add_action(
                thought="Determine jurisdiction options and recommendations.",
                action="jurisdiction_determination",
                action_input={"query": text},
            )
        if needs_hearing:
            add_action(
                thought="Generate hearing outline for trial preparation.",
                action="hearing_outline_generation",
                action_input={"outlineType": "trial_preparation"},
            )
        if needs_document:
            add_action(
                thought="Generate requested legal document draft.",
                action="document_generation",
                action_input={"draftType": "general"},
            )

        add_action(
            thought="Finalize with a consolidated risk assessment.",
            action="risk_assessment",
            action_input={"mode": "baseline"},
        )
        return self._slice_plan(actions)

    def plan_teacher(self, text: str, history: List[Dict[str, str]]) -> List[PlannedAction]:
        actions: List[PlannedAction] = []
        added = set()
        subject = self._infer_subject(text)
        grade = self._infer_grade(text)
        follow_up = self._is_teacher_follow_up(text=text, history=history)

        def add_action(thought: str, action: str, action_input: Dict[str, object]) -> None:
            if action in added:
                return
            added.add(action)
            merged_input = {
                "query": text,
                "subject": subject,
                "grade": grade,
                "historySize": len(history),
                **action_input,
            }
            actions.append(
                PlannedAction(
                    thought=thought,
                    action=action,
                    actionInput=merged_input,
                )
            )

        if follow_up:
            target_action = self._resolve_teacher_follow_up_action(text=text, history=history)
            if target_action:
                add_action(
                    thought="This is a follow-up refinement, execute only the requested teaching subtask.",
                    action=target_action,
                    action_input={"followUp": True, "mode": "incremental_update"},
                )
                return self._slice_plan(actions)

        needs_diagnosis = self._contains_any(
            text,
            [
                "学情",
                "诊断",
                "薄弱",
                "能力画像",
                "掌握度",
                "student profile",
                "diagnosis",
                "weak points",
            ],
        )
        needs_lesson_plan = self._contains_any(text, ["备课", "教案", "课堂流程", "lesson plan", "teaching plan"])
        needs_grading = self._contains_any(text, ["批改", "评分", "评语", "作文", "homework grading", "rubric"])
        needs_error_push = self._contains_any(text, ["错题", "归因", "推题", "变式", "error analysis", "similar questions"])
        needs_qa = self._contains_any(text, ["答疑", "讲解", "不会", "why", "how", "question", "explain"])
        needs_path = self._contains_any(text, ["学习路径", "学习计划", "周计划", "roadmap", "study plan"])
        needs_report = self._contains_any(text, ["学情报告", "阶段报告", "进步曲线", "report", "progress report"])
        needs_interaction = self._contains_any(text, ["课堂互动", "提问", "活动设计", "导入", "interaction", "activity"])
        needs_parent = self._contains_any(text, ["家长", "家校沟通", "沟通建议", "parent communication"])

        if needs_grading:
            add_action(
                thought="Start from grading output so correction feedback is immediately available.",
                action="homework_grading",
                action_input={},
            )
            if needs_error_push or self._contains_any(text, ["错题", "推题", "提升"]):
                add_action(
                    thought="Analyze mistakes and recommend targeted practice questions.",
                    action="error_analysis_question_push",
                    action_input={},
                )
            return self._slice_plan(actions)

        if needs_lesson_plan:
            if needs_diagnosis or self._contains_any(text, ["薄弱", "基础差", "学习困难", "弱项"]):
                add_action(
                    thought="Diagnose learner profile before generating a personalized lesson.",
                    action="student_diagnosis",
                    action_input={"enableFederated": True},
                )
            add_action(
                thought="Generate a personalized lesson plan from topic and learner context.",
                action="lesson_plan_generation",
                action_input={},
            )
            if needs_interaction or self._contains_any(text, ["导入", "互动", "提问"]):
                add_action(
                    thought="Design classroom interaction script aligned with the lesson plan.",
                    action="classroom_interaction_design",
                    action_input={},
                )
            return self._slice_plan(actions)

        if needs_report:
            add_action(
                thought="Build latest learner diagnosis as basis for report generation.",
                action="student_diagnosis",
                action_input={"enableFederated": True},
            )
            add_action(
                thought="Generate progress report with trends and recommendations.",
                action="progress_report_generation",
                action_input={},
            )
            return self._slice_plan(actions)

        if needs_path:
            add_action(
                thought="Assess current mastery before constructing study roadmap.",
                action="student_diagnosis",
                action_input={"enableFederated": True},
            )
            add_action(
                thought="Generate personalized weekly learning path.",
                action="learning_path_planning",
                action_input={},
            )
            return self._slice_plan(actions)

        if needs_parent:
            add_action(
                thought="Summarize learner strengths and gaps for parent-facing communication.",
                action="student_diagnosis",
                action_input={"enableFederated": True},
            )
            add_action(
                thought="Generate parent communication points and scripts.",
                action="parent_communication_suggestion",
                action_input={},
            )
            return self._slice_plan(actions)

        if needs_error_push:
            add_action(
                thought="Analyze wrong-question patterns and map knowledge gaps.",
                action="error_analysis_question_push",
                action_input={},
            )
            return self._slice_plan(actions)

        if needs_qa:
            add_action(
                thought="Provide guided tutoring answer with progressive hints.",
                action="tutoring_qa",
                action_input={},
            )
            return self._slice_plan(actions)

        if needs_interaction:
            add_action(
                thought="Design engagement-oriented classroom interaction strategy.",
                action="classroom_interaction_design",
                action_input={},
            )
            return self._slice_plan(actions)

        # Default full teacher chain for ambiguous requests.
        add_action(
            thought="Start from learner diagnosis to anchor personalization.",
            action="student_diagnosis",
            action_input={"enableFederated": True},
        )
        add_action(
            thought="Generate a baseline lesson plan for requested topic.",
            action="lesson_plan_generation",
            action_input={},
        )
        add_action(
            thought="Add a practical weekly learning roadmap.",
            action="learning_path_planning",
            action_input={},
        )
        return self._slice_plan(actions)

