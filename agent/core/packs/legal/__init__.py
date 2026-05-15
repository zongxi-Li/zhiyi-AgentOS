from pathlib import Path

from core.packs.legal.agents.case_intake import CaseIntakeAgent
from core.packs.legal.agents.draft import DraftAgent
from core.packs.legal.agents.evidence import EvidenceAgent
from core.packs.legal.agents.review import ReviewAgent
from core.packs.legal.agents.risk import RiskAgent
from core.packs.legal.agents.statute import StatuteAgent


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
