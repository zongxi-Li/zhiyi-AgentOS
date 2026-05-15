from core.agents.registry import AgentRegistry
from core.packs.legal import register_pack as register_legal_pack
from core.workflow_registry import WorkflowRegistry
from core.workflow_runtime import WorkflowRuntime


def build_default_runtime() -> WorkflowRuntime:
    """Build the default AgentOS Core runtime with installed demo packs."""

    agent_registry = AgentRegistry()
    workflow_registry = WorkflowRegistry()
    register_legal_pack(agent_registry=agent_registry, workflow_registry=workflow_registry)
    return WorkflowRuntime(agent_registry=agent_registry, workflow_registry=workflow_registry)
