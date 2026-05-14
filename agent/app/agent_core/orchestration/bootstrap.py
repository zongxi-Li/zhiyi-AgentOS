from app.agent_core.agents.registry import AgentRegistry
from app.agent_core.agents.packs.legal import register_pack as register_legal_pack
from app.agent_core.orchestration.workflow_registry import WorkflowRegistry
from app.agent_core.orchestration.workflow_runtime import WorkflowRuntime


def build_default_runtime() -> WorkflowRuntime:
    """Build the default AgentOS Core runtime with installed demo packs."""

    agent_registry = AgentRegistry()
    workflow_registry = WorkflowRegistry()
    register_legal_pack(agent_registry=agent_registry, workflow_registry=workflow_registry)
    return WorkflowRuntime(agent_registry=agent_registry, workflow_registry=workflow_registry)
