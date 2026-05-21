from typing import Dict, Iterable, Optional, Tuple

from agentos.agents.base import BaseAgent


class AgentNotFound(KeyError):
    """Raised when no agent matches a workflow step."""


class AgentRegistry:
    """Registry used by Core to resolve application-layer Pack agents."""

    def __init__(self):
        self._agents: Dict[Tuple[str, str], BaseAgent] = {}

    def register(self, agent: BaseAgent) -> None:
        domain = (agent.profile.domain or "").strip().lower()
        name = (agent.profile.agent_name or "").strip().lower()
        if not domain or not name:
            raise ValueError("agent domain and agentName are required")
        self._agents[(domain, name)] = agent

    def resolve(
        self,
        domain: str,
        agent_name: Optional[str] = None,
        capability: Optional[str] = None,
    ) -> BaseAgent:
        normalized_domain = (domain or "").strip().lower()
        normalized_name = (agent_name or "").strip().lower()

        if normalized_name:
            agent = self._agents.get((normalized_domain, normalized_name))
            if agent:
                return agent

        normalized_capability = (capability or "").strip().lower()
        if normalized_capability:
            for (agent_domain, _), agent in self._agents.items():
                if agent_domain != normalized_domain:
                    continue
                if normalized_capability in {item.lower() for item in agent.profile.capabilities}:
                    return agent

        raise AgentNotFound(
            f"agent not registered: domain={domain}, agentName={agent_name}, capability={capability}"
        )

    def all(self) -> Iterable[BaseAgent]:
        return tuple(self._agents.values())
