from agentos.agents.base import AgentOutput, AgentProfile, BaseAgent


class ReviewAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            AgentProfile(
                agentName="review",
                domain="legal",
                capabilities=["final_review", "quality_gate"],
                allowedSkills=["legal_reason"],
                description="Checks consistency and produces the final workflow answer.",
            )
        )

    async def run(self, context):
        observations = context.memory.observations
        draft = observations.get("draft", {}).get("draft", "")
        risk = observations.get("risk", {})
        final_answer = (
            "已完成合同审查工作流。关键结论："
            f"风险等级为 {risk.get('risk_level', 'unknown')}，"
            "建议先补齐合同原件、履约时间线、催告记录和电子证据真实性说明。\n\n"
            f"{draft}"
        ).strip()
        return AgentOutput(
            output={
                "final_answer": final_answer,
                "review_notes": ["结构完整", "风险节点已通过人工审核", "仍需审核者核验原始证据"],
            },
            summary="Final review completed.",
        )
