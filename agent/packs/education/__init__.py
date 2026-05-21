"""Education workflow pack."""

from pathlib import Path

from packs.education.agents import LessonPlanAgent


def register_pack(agent_registry, workflow_registry) -> None:
    """Register the education workflow pack."""

    agent_registry.register(LessonPlanAgent())
    workflow_registry.load_directory(Path(__file__).resolve().parent / "workflows")
