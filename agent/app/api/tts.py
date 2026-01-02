"""
语音合成API
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.aiservice import AIService

router = APIRouter()

# 依赖注入AI服务
ai_service = AIService()

class TtsRequest(BaseModel):
    """语音合成请求"""
    text: str
    voice: str = "default"
    speed: float = 1.0
    pitch: float = 1.0

@router.post("/tts")
async def text_to_speech(request: TtsRequest):
    """
    文本转语音
    
    Args:
        request: 语音合成请求，包含文本、语音类型、语速、音调
    
    Returns:
        音频数据（WAV格式）
    """
    audio_data = await ai_service.synthesize_speech(
        text=request.text,
        voice=request.voice,
        speed=request.speed,
        pitch=request.pitch
    )
    
    return {
        "audio": audio_data,
        "format": "wav",
        "text": request.text,
        "voice": request.voice,
        "speed": request.speed,
        "pitch": request.pitch
    }
