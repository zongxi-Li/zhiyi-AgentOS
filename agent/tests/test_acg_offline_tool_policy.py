from packs.legal.agents.recovery import LegalEvidenceRecoveryAgent
from packs.legal.agents.statute import StatuteAgent


def test_legal_retrieval_agents_declare_only_bounded_read_only_tools():
    assert set(StatuteAgent().profile.allowed_tools) == {
        "web_search",
        "knowledge_search",
        "current_datetime",
    }
    assert set(LegalEvidenceRecoveryAgent().profile.allowed_tools) == {
        "web_search",
        "current_datetime",
    }
