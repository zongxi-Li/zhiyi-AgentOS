"""
语音服务适配器
支持阿里云语音识别（ASR）和语音合成（TTS）API
使用DashScope API，与通义千问共用API密钥
"""
import logging
import base64
import httpx
from typing import Dict, Optional, AsyncIterator
import json

logger = logging.getLogger(__name__)


class SpeechAdapter:
    """语音服务适配器（ASR + TTS）"""
    
    def __init__(self, api_key: str):
        """
        初始化语音服务适配器
        
        Args:
            api_key: DashScope API密钥（与通义千问共用）
        """
        self.api_key = api_key
        self.base_url = "https://dashscope.aliyuncs.com/api/v1"
        self.client = httpx.AsyncClient(timeout=60.0)
        logger.info("语音服务适配器初始化成功")
    
    async def recognize_speech(
        self,
        audio_data: bytes,
        language: str = "zh-CN",
        format: str = "wav",
        sample_rate: int = 16000,
        **kwargs
    ) -> Dict:
        """
        语音识别（ASR）
        
        Args:
            audio_data: 音频数据（字节流）
            language: 语言代码（zh-CN/en-US等）
            format: 音频格式（wav/pcm/mp3等）
            sample_rate: 采样率（8000/16000等）
            **kwargs: 其他参数
        
        Returns:
            包含text、confidence、duration等的字典
        """
        try:
            # 阿里云DashScope ASR API端点
            # 注意：实际API端点可能不同，需要根据官方文档调整
            asr_url = f"{self.base_url}/services/audio/asr/transcription"
            
            # 将音频数据编码为base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            # 构建请求数据
            request_data = {
                "model": "paraformer-realtime-v2",  # 实时语音识别模型
                "input": {
                    "audio": audio_base64
                },
                "parameters": {
                    "format": format,
                    "sample_rate": sample_rate,
                    "language": language,
                    "enable_punctuation": True,  # 启用标点符号
                    "enable_word_timestamp": False  # 是否返回词级时间戳
                }
            }
            
            # 调用API
            response = await self.client.post(
                asr_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=request_data
            )
            
            # 检查响应状态
            response.raise_for_status()
            result = response.json()
            
            # 解析响应 - 兼容多种响应格式
            text = ""
            confidence = 0.0
            duration = 0.0
            
            # 尝试多种响应格式解析
            if result.get("output"):
                output = result["output"]
                # 格式1: output.sentence.text
                if isinstance(output, dict):
                    sentence = output.get("sentence", {})
                    if isinstance(sentence, dict):
                        text = sentence.get("text", "")
                        confidence = sentence.get("confidence", 0.0)
                    # 格式2: output.text (直接文本)
                    elif not text:
                        text = output.get("text", "")
                    duration = output.get("duration", 0.0)
            # 格式3: 直接在result中
            elif result.get("text"):
                text = result.get("text", "")
                confidence = result.get("confidence", 0.9)
                duration = result.get("duration", 0.0)
            
            if text:
                logger.info(f"语音识别成功: {len(text)} 字符, 置信度: {confidence:.2f}")
                return {
                    "text": text,
                    "confidence": confidence,
                    "duration": duration,
                    "language": language,
                    "success": True
                }
            else:
                error_msg = result.get("message", result.get("error", "API返回格式错误"))
                logger.error(f"语音识别API返回错误: {result}")
                raise ValueError(f"语音识别API错误: {error_msg}")
                
        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_response = e.response.json()
                error_detail = error_response.get("message", error_response.get("error", str(e)))
            except:
                error_detail = str(e)
            
            logger.error(f"语音识别API HTTP错误: {error_detail}")
            raise Exception(f"语音识别API调用失败: {error_detail}")
        except Exception as e:
            logger.error(f"语音识别API调用异常: {e}", exc_info=True)
            raise
    
    async def synthesize_speech(
        self,
        text: str,
        voice: str = "zhitian_emo",
        speed: float = 1.0,
        pitch: float = 1.0,
        format: str = "wav",
        sample_rate: int = 16000,
        **kwargs
    ) -> bytes:
        """
        语音合成（TTS）
        
        Args:
            text: 要合成的文本
            voice: 语音类型（zhitian_emo/zhitian_tech/zhimiao_emo等）
            speed: 语速（0.5-2.0，默认1.0）
            pitch: 音调（0.5-2.0，默认1.0）
            format: 音频格式（wav/pcm/mp3）
            sample_rate: 采样率（8000/16000/24000）
            **kwargs: 其他参数
        
        Returns:
            音频数据（字节流）
        """
        try:
            # 限制参数范围
            speed = max(0.5, min(2.0, speed))
            pitch = max(0.5, min(2.0, pitch))
            
            # 映射前端语音类型到阿里云语音ID
            voice_mapping = {
                "default": "zhitian_emo",
                "female": "zhimiao_emo",
                "male": "zhitian_tech",
                "gentle": "zhitian_emo",
                "lively": "zhimiao_emo"
            }
            actual_voice = voice_mapping.get(voice, voice)
            
            # 阿里云DashScope TTS API端点
            tts_url = f"{self.base_url}/services/audio/tts/text-to-speech"
            
            # 构建请求数据
            request_data = {
                "model": "sambert-zhitian-v1",  # 语音合成模型
                "input": {
                    "text": text
                },
                "parameters": {
                    "voice": actual_voice,
                    "format": format,
                    "sample_rate": sample_rate,
                    "speed": speed,
                    "pitch": pitch
                }
            }
            
            # 调用API
            response = await self.client.post(
                tts_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=request_data
            )
            
            # 检查响应状态
            response.raise_for_status()
            result = response.json()
            
            # 解析响应 - 兼容多种响应格式
            audio_base64 = ""
            
            # 格式1: output.audio
            if result.get("output"):
                output = result["output"]
                if isinstance(output, dict):
                    audio_base64 = output.get("audio", "")
            
            # 格式2: 直接在result中
            if not audio_base64:
                audio_base64 = result.get("audio", "")
            
            if audio_base64:
                # 解码base64音频数据
                audio_data = base64.b64decode(audio_base64)
                logger.info(f"语音合成成功: {len(text)} 字符, 音频长度: {len(audio_data)} 字节")
                return audio_data
            else:
                error_msg = result.get("message", result.get("error", "API返回格式错误"))
                logger.error(f"语音合成API返回错误: {result}")
                raise ValueError(f"语音合成API错误: {error_msg}")
                
        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_response = e.response.json()
                error_detail = error_response.get("message", error_response.get("error", str(e)))
            except:
                error_detail = str(e)
            
            logger.error(f"语音合成API HTTP错误: {error_detail}")
            raise Exception(f"语音合成API调用失败: {error_detail}")
        except Exception as e:
            logger.error(f"语音合成API调用异常: {e}", exc_info=True)
            raise
    
    async def recognize_speech_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        language: str = "zh-CN",
        format: str = "pcm",
        sample_rate: int = 16000,
        **kwargs
    ) -> AsyncIterator[Dict]:
        """
        流式语音识别（实时ASR）
        
        Args:
            audio_stream: 音频流（异步迭代器）
            language: 语言代码
            format: 音频格式
            sample_rate: 采样率
            **kwargs: 其他参数
        
        Yields:
            识别结果字典（包含partial_text和final_text）
        """
        try:
            # 阿里云流式ASR API端点
            stream_asr_url = f"{self.base_url}/services/audio/asr/transcription-stream"
            
            # 构建请求头
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # 流式发送音频数据
            async for audio_chunk in audio_stream:
                # 将音频块编码为base64
                audio_base64 = base64.b64encode(audio_chunk).decode('utf-8')
                
                # 构建请求数据
                request_data = {
                    "model": "paraformer-realtime-v2",
                    "input": {
                        "audio": audio_base64
                    },
                    "parameters": {
                        "format": format,
                        "sample_rate": sample_rate,
                        "language": language,
                        "enable_punctuation": True,
                        "enable_partial_result": True  # 启用部分结果
                    }
                }
                
                # 调用API
                response = await self.client.post(
                    stream_asr_url,
                    headers=headers,
                    json=request_data
                )
                
                response.raise_for_status()
                result = response.json()
                
                # 解析响应
                if result.get("output"):
                    output = result["output"]
                    sentence = output.get("sentence", {})
                    
                    yield {
                        "text": sentence.get("text", ""),
                        "confidence": sentence.get("confidence", 0.0),
                        "is_final": sentence.get("is_final", False),
                        "partial_text": sentence.get("partial_text", ""),
                        "success": True
                    }
                else:
                    error_msg = result.get("message", "API返回格式错误")
                    logger.warning(f"流式识别API返回错误: {error_msg}")
                    yield {
                        "text": "",
                        "confidence": 0.0,
                        "is_final": False,
                        "success": False,
                        "error": error_msg
                    }
                    
        except Exception as e:
            logger.error(f"流式语音识别异常: {e}", exc_info=True)
            yield {
                "text": "",
                "confidence": 0.0,
                "is_final": False,
                "success": False,
                "error": str(e)
            }
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()

