from pathlib import Path

from packs.legal.agents.case_intake import CaseIntakeAgent
from packs.legal.agents.draft import DraftAgent
from packs.legal.agents.evidence import EvidenceAgent
from packs.legal.agents.review import ReviewAgent
from packs.legal.agents.risk import RiskAgent
from packs.legal.agents.statute import StatuteAgent


def register_pack(agent_registry, workflow_registry) -> None:
    """Register the legal demo pack without coupling Core to legal logic."""

    for agent in [
        CaseIntakeAgent(),
        StatuteAgent(),
        EvidenceAgent(),
        RiskAgent(),
        DraftAgent(),
        ReviewAgent(),
    ]:
        agent_registry.register(agent)

    workflow_registry.load_directory(Path(__file__).resolve().parent / "workflows")
