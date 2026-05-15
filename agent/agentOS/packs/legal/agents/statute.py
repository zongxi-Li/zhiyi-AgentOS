from agentos.agents.base import AgentOutput, AgentProfile, BaseAgent
from agentos.packs.legal.agents.common import case_text, has_any


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
        basis = [
            {
                "lawName": "中华人民共和国民法典",
                "article": "第五百零九条",
                "title": "合同履行原则",
                "reason": "合同当事人应按照约定全面履行义务。",
            },
            {
                "lawName": "中华人民共和国民法典",
                "article": "第五百七十七条",
                "title": "违约责任",
                "reason": "一方不履行合同义务或履行不符合约定的，应承担违约责任。",
            },
        ]
        if has_any(text, ["逾期", "延期", "迟延"]):
            basis.append(
                {
                    "lawName": "中华人民共和国民法典",
                    "article": "第五百八十五条",
                    "title": "违约金调整",
                    "reason": "涉及逾期违约金约定时需要审查是否过高或过低。",
                }
            )

        return AgentOutput(
            output={"legal_basis": basis, "query": text[:120]},
            summary=f"Statute retrieval completed with {len(basis)} legal basis item(s).",
        )
