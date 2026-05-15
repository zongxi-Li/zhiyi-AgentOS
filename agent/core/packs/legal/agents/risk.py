from core.agents.base import AgentOutput, AgentProfile, BaseAgent


class RiskAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            AgentProfile(
                agentName="risk",
                domain="legal",
                capabilities=["risk_assessment", "human_review_gate"],
                allowedSkills=["risk_assessment"],
                riskLevel="high",
                description="Scores legal risk and creates a human-review gate for sensitive legal workflows.",
            )
        )

    async def run(self, context):
        observations = context.memory.observations
        intake = observations.get("case_intake", {})
        evidence = observations.get("evidence", {})
        legal_basis = observations.get("statute", {}).get("legal_basis", [])

        score = 35
        missing = evidence.get("missing_evidence", [])
        if len(missing) >= 3:
            score += 20
        if len(legal_basis) < 2:
            score += 20
        if "电子证据真实性" in intake.get("legal_issues", []):
            score += 10

        level = "high" if score >= 70 else "medium" if score >= 45 else "low"
        output = {
            "risk_level": level,
            "risk_score": min(score, 100),
            "key_risks": [
                "证据真实性和完整性需人工核验",
                "合同履行节点与违约责任需结合原文确认",
            ],
            "mitigation_suggestions": [
                "补充合同原件、履约记录和催告材料",
                "由审核者确认风险结论后再进入文书草拟",
            ],
            "review_required": True,
        }
        return AgentOutput(output=output, summary=f"Risk assessed as {level}.", riskLevel=level)
