from core.adapters.retrieval_adapter import legal_index_builder
from core.types import SkillRequest, SkillResult
from core.skills.base import BaseSkill


class CaseRetrievalSkill(BaseSkill):
    def __init__(self):
        super().__init__("case_retrieval")

    async def run(self, request: SkillRequest) -> SkillResult:
        query = request.action_input.get("query") or request.text
        top_k = int(request.action_input.get("top_k", 5))
        rows = legal_index_builder.search_cases(query=query, top_k=top_k)

        cases = []
        for row in rows:
            metadata = row.get("metadata", {})
            cases.append(
                {
                    "title": metadata.get("title", ""),
                    "caseNo": metadata.get("case_no", ""),
                    "court": metadata.get("court", ""),
                    "score": row.get("score", 0.0),
                    "summary": row.get("content", ""),
                    "source": metadata.get("source", ""),
                }
            )

        return SkillResult(
            skillName=self.name,
            success=True,
            output={
                "query": query,
                "count": len(cases),
                "cases": cases,
            },
            message=f"Retrieved {len(cases)} case candidates.",
        )

