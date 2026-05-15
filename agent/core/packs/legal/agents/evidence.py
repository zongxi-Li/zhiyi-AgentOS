from core.agents.base import AgentOutput, AgentProfile, BaseAgent
from core.packs.legal.agents.common import case_text, dedupe, has_any


class EvidenceAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            AgentProfile(
                agentName="evidence",
                domain="legal",
                capabilities=["evidence_analysis"],
                allowedSkills=["evidence_analysis"],
                description="Assesses evidence strength and missing materials.",
            )
        )

    async def run(self, context):
        text = case_text(context.task.input)
        items = []
        if has_any(text, ["转账", "付款", "银行"]):
            items.append({"name": "转账/付款记录", "type": "书证/电子数据", "strength": "strong"})
        if has_any(text, ["微信", "聊天", "邮件"]):
            items.append({"name": "沟通记录", "type": "电子数据", "strength": "medium"})
        if has_any(text, ["合同", "协议"]):
            items.append({"name": "合同文本", "type": "书证", "strength": "strong"})

        gaps = ["合同原件或盖章扫描件", "履行及违约时间线", "催告或协商记录"]
        if items:
            gaps = dedupe(gaps + ["证据来源与真实性说明"])

        output = {
            "evidence_items": items,
            "missing_evidence": gaps,
            "overall_assessment": "现有材料可形成初步证据链，但仍需补强原件、时间线和真实性说明。",
        }
        return AgentOutput(output=output, summary=f"Evidence analysis completed with {len(items)} item(s).")
