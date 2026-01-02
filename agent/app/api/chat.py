"""
对话API路由
"""
from fastapi import APIRouter, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Dict, Optional
from app.services.aiservice import AIService

router = APIRouter()

# 依赖注入AI服务
ai_service = AIService()

class ChatRequest(BaseModel):
    text: str
    role_id: Optional[str] = None
    context: Optional[List[Dict[str, str]]] = None

class ChatResponse(BaseModel):
    text: str
    confidence: float
    tokens_used: int
    animation: Optional[Dict] = None

@router.post("/chat/text", response_model=ChatResponse)
async def chat_text(request: ChatRequest):
    """文本对话"""
    response = await ai_service.generate_text(
        text=request.text,
        role_id=request.role_id,
        context=request.context
    )
    return ChatResponse(
        text=response.get("text", ""),
        confidence=response.get("confidence", 0.85),
        tokens_used=response.get("tokens_used", 0),
        animation=response.get("animation")
    )

@router.post("/chat/voice")
async def chat_voice(
    audio: UploadFile = File(...),
    role_id: Optional[str] = Form(None)
):
    """语音对话"""
    audio_data = await audio.read()
    response = await ai_service.recognize_speech(audio_data)
    
    # 根据识别的文本生成回复
    chat_response = await ai_service.generate_text(
        text=response["text"],
        role_id=role_id
    )
    
    return {
        "text": chat_response["text"],
        "confidence": chat_response["confidence"],
        "recognized_text": response["text"]
    }

