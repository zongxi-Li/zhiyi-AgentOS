from agentos.agents.base import AgentOutput, AgentProfile, BaseAgent


class OutlineGenerateAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            AgentProfile(
                agentName="outline_generate",
                domain="writer",
                capabilities=["story_outline", "outline_generate"],
                allowedSkills=["outline_generate"],
                description="Creates a minimal story outline from a writing premise.",
            )
        )

    async def run(self, context):
        task_input = context.task.input
        premise = str(task_input.get("premise") or context.task.title).strip()
        genre = str(task_input.get("genre") or "fiction").strip()
        outline = {
            "premise": premise,
            "genre": genre,
            "chapters": [
                {"chapter": 1, "goal": "Introduce the protagonist and central tension."},
                {"chapter": 2, "goal": "Escalate conflict and reveal the hidden cost."},
                {"chapter": 3, "goal": "Resolve the core choice with a changed protagonist."},
            ],
        }
        return AgentOutput(
            output={
                "outline": outline,
                "final_answer": f"Story outline ready for {genre}: {premise}.",
            },
            summary="Story outline generated.",
        )
