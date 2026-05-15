"""Model adapter seam used by Core and built-in skills."""

from typing import Dict, List, Optional

from core.adapters.model_adapter import AIService


class ModelAdapter:
    """Thin wrapper around the current AIService implementation."""

    def __init__(self, ai_service: Optional[AIService] = None):
        self.ai_service = ai_service or AIService()

    async def generate_text(
        self,
        text: str,
        role_id: Optional[str] = None,
        context: Optional[List[Dict[str, str]]] = None,
    ) -> Dict:
        return await self.ai_service.generate_text(text=text, role_id=role_id, context=context)


__all__ = ["AIService", "ModelAdapter"]
