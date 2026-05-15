from agentos.agents.base import AgentOutput, AgentProfile, BaseAgent


class LessonPlanAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            AgentProfile(
                agentName="lesson_plan",
                domain="education",
                capabilities=["lesson_plan", "teaching_design"],
                allowedSkills=["lesson_plan_generation"],
                description="Creates a minimal lesson plan from teaching task input.",
            )
        )

    async def run(self, context):
        task_input = context.task.input
        topic = str(task_input.get("topic") or context.task.title).strip()
        subject = str(task_input.get("subject") or "general").strip()
        grade = str(task_input.get("grade") or "general").strip()
        plan = {
            "topic": topic,
            "subject": subject,
            "grade": grade,
            "objectives": [
                f"Understand the core concept of {topic}.",
                "Practice with guided examples.",
                "Summarize common mistakes and next steps.",
            ],
            "activities": [
                "Warm-up diagnosis",
                "Concept explanation",
                "Practice and feedback",
            ],
        }
        return AgentOutput(
            output={
                "lesson_plan": plan,
                "final_answer": f"Lesson plan ready for {grade} {subject}: {topic}.",
            },
            summary="Lesson plan generated.",
        )
