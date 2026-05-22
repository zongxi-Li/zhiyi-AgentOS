"""AgentOS Core 的智能体基础接口，定义 AgentProfile、AgentOutput、运行上下文和 BaseAgent。"""


from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from agentos.core.models.types import AgentTask, WorkflowDefinition, WorkflowRun, WorkflowStep


class AgentProfile(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    agent_name: str = Field(alias="agentName")
    domain: str
    capabilities: List[str] = Field(default_factory=list)
    allowed_skills: List[str] = Field(default_factory=list, alias="allowedSkills")
    risk_level: str = Field(default="normal", alias="riskLevel")
    description: str = ""


class AgentOutput(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    output: Dict[str, Any] = Field(default_factory=dict)
    summary: str = ""
    risk_level: Optional[str] = Field(default=None, alias="riskLevel")


class AgentRunContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    task: AgentTask
    run: WorkflowRun
    workflow: WorkflowDefinition
    step: WorkflowStep
    memory: Any


class BaseAgent(ABC):
    """所有应用层 Pack 智能体的统一接口。"""

    def __init__(self, profile: AgentProfile):
        self.profile = profile

    @abstractmethod
    async def run(self, context: AgentRunContext) -> AgentOutput:
        raise NotImplementedError

    async def review(self, context: AgentRunContext) -> AgentOutput:
        return await self.run(context)
