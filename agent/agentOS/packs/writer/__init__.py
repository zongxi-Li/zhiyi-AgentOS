"""Writer workflow pack."""

from pathlib import Path

from agentos.packs.writer.agents import OutlineGenerateAgent


def register_pack(agent_registry, workflow_registry) -> None:
    """Register the writer workflow pack."""

    agent_registry.register(OutlineGenerateAgent())
    workflow_registry.load_directory(Path(__file__).resolve().parent / "workflows")
