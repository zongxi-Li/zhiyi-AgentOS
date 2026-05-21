"""Model adapter seam used by Core and built-in skills."""

from typing import Any, Dict, List, Optional


class AIService:
    """Lazy bridge to the application AI service.

    AgentOS Core must be importable without importing the FastAPI app layer.
    The concrete app service is loaded only when text generation is invoked.
    """

    def __init__(self, delegate: Optional[Any] = None):
        self._delegate = delegate

    def _resolve_delegate(self) -> Any:
        if self._delegate is None:
            from app.services.aiservice import AIService as AppAIService

            self._delegate = AppAIService()
        return self._delegate

    async def generate_text(
        self,
        text: str,
        role_id: Optional[str] = None,
        context: Optional[List[Dict[str, str]]] = None,
    ) -> Dict:
        return await self._resolve_delegate().generate_text(text=text, role_id=role_id, context=context)


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
