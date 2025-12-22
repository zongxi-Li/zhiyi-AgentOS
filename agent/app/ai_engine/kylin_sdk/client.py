"""
麒麟AI SDK客户端封装
"""
import logging
from typing import List, Dict, Optional
import httpx

logger = logging.getLogger(__name__)

# 全局标志：是否已打印API key警告
_api_key_warning_printed = False

class KylinSDKClient:
    """麒麟AI SDK客户端"""
    
    def __init__(self, api_key: str, api_endpoint: str, timeout: int = 30):
        """
        初始化客户端
        
        Args:
            api_key: API密钥
            api_endpoint: API端点
            timeout: 超时时间（秒）
        """
        self.api_key = api_key
        self.api_endpoint = api_endpoint.rstrip('/')
        self.timeout = timeout
        self.client = httpx.AsyncClient(
            base_url=self.api_endpoint,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=timeout
        )
        logger.info(f"Kylin AI SDK Client initialized: {api_endpoint}")
    
    async def generate_text(
        self,
        prompt: str,
        context: Optional[List[Dict[str, str]]] = None,
        role_config: Optional[Dict] = None,
        **kwargs
    ) -> Dict:
        """
        文本生成
        
        Args:
            prompt: 输入提示
            context: 对话上下文
            role_config: 角色配置
            **kwargs: 其他参数
        
        Returns:
            生成的文本和元数据
        """
        try:
            request_data = {
                "prompt": prompt,
                "max_tokens": kwargs.get("max_tokens", 512),
                "temperature": kwargs.get("temperature", 0.7),
                "top_p": kwargs.get("top_p", 0.9),
            }
            
            if context:
                request_data["context"] = context
            
            if role_config:
                request_data["system_prompt"] = role_config.get("system_prompt")
                request_data["style"] = role_config.get("style")
            
            # TODO: 实际调用麒麟AI SDK API
            # response = await self.client.post("/v1/text/generate", json=request_data)
            # return response.json()
            
            # 临时模拟响应
            logger.warning("使用模拟响应，请集成实际SDK")
            return {
                "text": f"这是对'{prompt}'的AI回复（模拟）",
                "confidence": 0.95,
                "tokens_used": 150
            }
            
        except Exception as e:
            logger.error(f"Text generation error: {e}")
            raise
    
    async def recognize_speech(
        self,
        audio_data: bytes,
        language: str = "zh-CN",
        **kwargs
    ) -> Dict:
        """
        语音识别
        
        Args:
            audio_data: 音频数据
            language: 语言代码
            **kwargs: 其他参数
        
        Returns:
            识别的文本和元数据
        """
        try:
            # TODO: 实际调用麒麟AI SDK API
            # files = {"audio": audio_data}
            # response = await self.client.post(
            #     "/v1/speech/recognize",
            #     files=files,
            #     params={"language": language}
            # )
            # return response.json()
            
            # 临时模拟响应
            logger.warning("使用模拟响应，请集成实际SDK")
            return {
                "text": "这是语音识别的结果（模拟）",
                "confidence": 0.92,
                "duration": 3.5
            }
            
        except Exception as e:
            logger.error(f"Speech recognition error: {e}")
            raise
    
    async def synthesize_speech(
        self,
        text: str,
        voice: str = "default",
        speed: float = 1.0,
        pitch: float = 1.0,
        **kwargs
    ) -> bytes:
        """
        语音合成
        
        Args:
            text: 要合成的文本
            voice: 语音类型
            speed: 语速
            pitch: 音调
            **kwargs: 其他参数
        
        Returns:
            音频数据
        """
        try:
            request_data = {
                "text": text,
                "voice": voice,
                "speed": speed,
                "pitch": pitch
            }
            
            # TODO: 实际调用麒麟AI SDK API
            # response = await self.client.post("/v1/speech/synthesize", json=request_data)
            # return response.content
            
            # 临时返回空音频
            logger.warning("使用模拟响应，请集成实际SDK")
            return b""
            
        except Exception as e:
            logger.error(f"Speech synthesis error: {e}")
            raise
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()


class KylinAIClient:
    """
    麒麟AI客户端包装类
    自动从配置读取参数，提供更便捷的初始化方式
    """
    
    def __init__(self, api_key: Optional[str] = None, api_endpoint: Optional[str] = None, timeout: Optional[int] = None):
        """
        初始化客户端
        
        Args:
            api_key: API密钥（可选，默认从配置读取）
            api_endpoint: API端点（可选，默认从配置读取）
            timeout: 超时时间（可选，默认从配置读取）
        """
        # 尝试从配置导入
        try:
            from app.config import settings
            self._api_key = api_key or getattr(settings, 'KYLIN_AI_API_KEY', '')
            self._api_endpoint = api_endpoint or getattr(settings, 'KYLIN_AI_ENDPOINT', 'https://api.kylin.ai')
            self._timeout = timeout or getattr(settings, 'KYLIN_AI_TIMEOUT', 30)
        except Exception as e:
            logger.warning(f"无法从配置读取参数，使用默认值: {e}")
            self._api_key = api_key or ''
            self._api_endpoint = api_endpoint or 'https://api.kylin.ai'
            self._timeout = timeout or 30
        
        # 如果API key为空，记录警告（开发环境可以使用模拟响应）
        global _api_key_warning_printed
        if not self._api_key and not _api_key_warning_printed:
            logger.warning("KYLIN_AI_API_KEY 未设置，将使用模拟响应。开发环境可以使用模拟响应进行测试。")
            logger.warning("如需使用真实API，请设置环境变量 KYLIN_AI_API_KEY 或创建 .env 文件。")
            _api_key_warning_printed = True
        
        # 创建底层SDK客户端
        self._sdk_client = KylinSDKClient(
            api_key=self._api_key,
            api_endpoint=self._api_endpoint,
            timeout=self._timeout
        )
    
    async def generate_text(
        self,
        text: Optional[str] = None,
        prompt: Optional[str] = None,
        role_id: Optional[str] = None,
        context: Optional[List[Dict[str, str]]] = None,
        **kwargs
    ) -> Dict:
        """
        生成文本回复
        
        Args:
            text: 用户输入文本（与prompt二选一）
            prompt: 输入提示（与text二选一）
            role_id: 角色ID（可选）
            context: 对话上下文（可选）
            **kwargs: 其他参数
        
        Returns:
            包含text、confidence、tokens_used等的字典
        """
        # 支持text和prompt两种参数名
        prompt_text = text or prompt
        if not prompt_text:
            raise ValueError("必须提供text或prompt参数")
        
        # 如果有role_id，可以转换为role_config（简化实现）
        role_config = None
        if role_id:
            # 这里可以根据role_id获取角色配置，暂时使用简化实现
            role_config = {
                "role_id": role_id,
                "system_prompt": f"你是一个专业的AI助手，角色ID: {role_id}",
                "style": "professional"
            }
        
        return await self._sdk_client.generate_text(
            prompt=prompt_text,
            context=context,
            role_config=role_config,
            **kwargs
        )
    
    async def recognize_speech(self, audio_data: bytes, **kwargs) -> Dict:
        """
        语音识别
        
        Args:
            audio_data: 音频数据
            **kwargs: 其他参数
        
        Returns:
            包含text和confidence的字典
        """
        return await self._sdk_client.recognize_speech(audio_data, **kwargs)
    
    async def synthesize_speech(
        self,
        text: str,
        voice: str = "default",
        speed: float = 1.0,
        pitch: float = 1.0,
        **kwargs
    ) -> bytes:
        """
        语音合成
        
        Args:
            text: 要合成的文本
            voice: 语音类型
            speed: 语速
            pitch: 音调
            **kwargs: 其他参数
        
        Returns:
            音频数据
        """
        return await self._sdk_client.synthesize_speech(
            text=text,
            voice=voice,
            speed=speed,
            pitch=pitch,
            **kwargs
        )
    
    async def close(self):
        """关闭客户端"""
        await self._sdk_client.close()