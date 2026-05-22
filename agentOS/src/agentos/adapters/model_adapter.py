"""AgentOS Core 的适配器 model_adapter 模块，连接模型、检索和联邦增强等外部能力。"""



from typing import Any, Dict, List, Optional


class AIService:
    """延迟桥接应用层 AIService，避免 Core 在导入阶段绑定应用服务。"""

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
    """当前 AIService 实现的轻量包装。"""

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
