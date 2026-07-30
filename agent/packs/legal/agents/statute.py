"""Legal basis retrieval backed by local and public read-only evidence tools."""

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
                allowedTools=[
                    "knowledge_search",
                    "current_datetime",
                ],
                description="Finds legal basis for the current dispute and preserves its sources.",
            )
        )

    async def run(self, context):
        text = case_text(context.task.input)
        if context.tool_runtime is None:
            raise RuntimeError("legal evidence tool runtime is not configured")
        result = await context.tool_runtime.run(
            "Find the currently applicable legal basis for the following matter. "
            "Prefer authoritative sources and distinguish binding law from commentary.\n\n"
            f"Matter: {text[:4000]}",
            require_evidence=True,
        )
        sources = [item.public_dict() for item in result.sources]
        evidence_refs = [item.citation_id for item in result.sources]
        if not evidence_refs:
            raise RuntimeError("legal basis retrieval requires evidence but no source was returned")
        return AgentOutput(
            output={
                "legal_basis": [result.text],
                "query": text[:500],
                "retrieval_status": "completed",
                "sources": sources,
                "evidence_refs": evidence_refs,
            },
            summary=f"Retrieved legal basis from {len(evidence_refs)} source(s).",
            sources=sources,
            toolExecutions=[item.public_dict() for item in result.tool_executions],
            evidenceRefs=evidence_refs,
        )
