from agentos.agents import AgentRegistry
from agentos.core.workflow_registry import WorkflowRegistry
from agentos.packs.registry import discover_pack_manifests, register_installed_packs


def test_pack_registry_discovers_installed_manifests():
    manifests = discover_pack_manifests()

    assert {manifest.pack_id for manifest in manifests} >= {
        "education",
        "legal",
        "programmer",
        "writer",
    }
    assert next(manifest for manifest in manifests if manifest.pack_id == "legal").module == "agentos.packs.legal"


def test_pack_registry_registers_enabled_packs_from_manifest():
    agent_registry = AgentRegistry()
    workflow_registry = WorkflowRegistry()

    registered = register_installed_packs(
        agent_registry=agent_registry,
        workflow_registry=workflow_registry,
    )

    assert "legal" in {manifest.pack_id for manifest in registered}
    assert workflow_registry.get("legal_case_analysis_v1").domain == "legal"
    assert agent_registry.resolve("legal", agent_name="case_intake").profile.agent_name == "case_intake"
