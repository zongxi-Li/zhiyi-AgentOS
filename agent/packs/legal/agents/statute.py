"""法律 Pack 的智能体实现，负责法律工作流中的专业步骤执行。"""


from agentos.agents.base import AgentOutput, AgentProfile, BaseAgent
from packs.legal.agents.common import case_text


class StatuteAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            AgentProfile(
                agentName="statute",
                domain="legal",
                capabilities=["statute_retrieval", "legal_basis"],
                allowedSkills=["statute_retrieval", "case_retrieval"],
                description="Finds legal basis for the workflow's current dispute.",
            )
        )

    async def run(self, context):
        text = case_text(context.task.input)
        return AgentOutput(
            output={"legal_basis": [], "query": text[:120], "retrieval_status": "unavailable"},
            summary="No statute result was generated.",
        )
