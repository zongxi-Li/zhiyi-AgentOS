from agentos.adapters.retrieval_adapter import legal_index_builder
from agentos.core.types import SkillRequest, SkillResult
from agentos.skills.base import BaseSkill


class StatuteRetrievalSkill(BaseSkill):
    def __init__(self):
        super().__init__("statute_retrieval")

    async def run(self, request: SkillRequest) -> SkillResult:
        query = request.action_input.get("query") or request.text
        top_k = int(request.action_input.get("top_k", 5))
        rows = legal_index_builder.search_statutes(query=query, top_k=top_k)

        statutes = []
        for row in rows:
            metadata = row.get("metadata", {})
            statutes.append(
                {
                    "title": metadata.get("title", ""),
                    "lawName": metadata.get("law_name", ""),
                    "article": metadata.get("article", ""),
                    "score": row.get("score", 0.0),
                    "content": row.get("content", ""),
                    "source": metadata.get("source", ""),
                }
            )

        return SkillResult(
            skillName=self.name,
            success=True,
            output={
                "query": query,
                "count": len(statutes),
                "statutes": statutes,
            },
            message=f"Retrieved {len(statutes)} statute candidates.",
        )

