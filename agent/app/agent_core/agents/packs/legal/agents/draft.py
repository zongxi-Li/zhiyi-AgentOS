from app.agent_core.agents.base import AgentOutput, AgentProfile, BaseAgent


class DraftAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            AgentProfile(
                agentName="draft",
                domain="legal",
                capabilities=["document_draft"],
                allowedSkills=["document_generation"],
                description="Drafts a legal deliverable from upstream workflow artifacts.",
            )
        )

    async def run(self, context):
        observations = context.memory.observations
        intake = observations.get("case_intake", {})
        statute = observations.get("statute", {})
        evidence = observations.get("evidence", {})
        risk = observations.get("risk", {})

        basis_lines = [
            f"- {item.get('lawName')} {item.get('article')}：{item.get('title')}"
            for item in statute.get("legal_basis", [])[:3]
        ]
        draft = (
            "# 合同审查初步意见\n\n"
            "## 一、案情摘要\n"
            f"{intake.get('case_summary', '案情待补充')}\n\n"
            "## 二、主要争议\n"
            f"{'；'.join(intake.get('legal_issues', [])) or '争议焦点待明确'}\n\n"
            "## 三、参考依据\n"
            f"{chr(10).join(basis_lines) if basis_lines else '- 待补充法律依据'}\n\n"
            "## 四、证据情况\n"
            f"{evidence.get('overall_assessment', '证据情况待分析')}\n\n"
            "## 五、风险提示\n"
            f"风险等级：{risk.get('risk_level', 'unknown')}，分值：{risk.get('risk_score', 'N/A')}。\n"
        )
        return AgentOutput(
            output={"draft": draft, "document_type": "合同审查初步意见"},
            summary="Draft generated.",
        )
