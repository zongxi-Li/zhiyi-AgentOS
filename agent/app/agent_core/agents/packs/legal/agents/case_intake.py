from app.agent_core.agents.base import AgentOutput, AgentProfile, BaseAgent
from app.agent_core.agents.packs.legal.agents.common import case_text, has_any


class CaseIntakeAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            AgentProfile(
                agentName="case_intake",
                domain="legal",
                capabilities=["case_intake", "fact_extraction"],
                allowedSkills=["case_understanding"],
                description="Extracts facts, issues, and missing information from legal task input.",
            )
        )

    async def run(self, context):
        text = case_text(context.task.input) or context.task.title
        case_type = "合同纠纷" if has_any(text, ["合同", "违约", "交付", "付款"]) else "民商事争议"
        legal_issues = ["合同履行与违约责任"] if case_type == "合同纠纷" else ["事实认定", "请求权基础"]
        if has_any(text, ["转账", "付款", "银行"]):
            legal_issues.append("付款事实与金额认定")
        if has_any(text, ["微信", "聊天", "邮件"]):
            legal_issues.append("电子证据真实性")

        output = {
            "case_summary": text[:300] or "未提供案情文本",
            "case_type": case_type,
            "parties": ["甲方/申请人待明确", "乙方/相对方待明确"],
            "legal_issues": legal_issues,
            "claims": ["确认违约责任", "评估赔偿或继续履行可能性"],
            "missing_info": ["合同签署版本", "履行时间线", "违约通知与催告记录"],
        }
        return AgentOutput(output=output, summary="Case intake completed.")
