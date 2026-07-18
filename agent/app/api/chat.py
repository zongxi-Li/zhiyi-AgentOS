"""
对话API路由
"""
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import json
from app.services.aiservice import AIService
from app.ai_engine.kylin_sdk.client import KylinAIClient
from app.ai_engine.model_runtime import apply_reasoning_instruction, stream_with_runtime_model

router = APIRouter()

# 依赖注入AI服务
ai_service = AIService()
stream_client = KylinAIClient()

class ChatRequest(BaseModel):
    text: str
    role_id: Optional[str] = None
    context: Optional[List[Dict[str, str]]] = None
    model: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    reasoning_effort: str = "off"

class ChatResponse(BaseModel):
    text: str
    confidence: float
    tokens_used: int
    animation: Optional[Dict] = None
    model_info: Optional[str] = None

@router.post("/chat/text", response_model=ChatResponse)
async def chat_text(request: ChatRequest):
    """文本对话"""
    response = await ai_service.generate_text(
        text=request.text,
        role_id=request.role_id,
        context=request.context,
        model=request.model,
        base_url=request.base_url,
        api_key=request.api_key,
        reasoning_effort=request.reasoning_effort,
    )
    return ChatResponse(
        text=response.get("text", ""),
        confidence=response.get("confidence", 0.85),
        tokens_used=response.get("tokens_used", 0),
        animation=response.get("animation"),
        model_info=response.get("model"),
    )

@router.post("/chat/text/stream")
async def chat_text_stream(request: ChatRequest):
    """流式文本对话 (SSE)"""
    async def event_stream():
        try:
            if request.model or request.base_url or request.api_key:
                chunks = stream_with_runtime_model(
                    text=request.text,
                    context=request.context,
                    model=request.model or "",
                    base_url=request.base_url or "",
                    api_key=request.api_key or "",
                    reasoning_effort=request.reasoning_effort,
                )
            else:
                text = request.text
                if request.reasoning_effort != "off":
                    messages = apply_reasoning_instruction(
                        [{"role": "user", "content": text}], request.reasoning_effort
                    )
                    text = "\n".join(item["content"] for item in messages)
                chunks = stream_client.generate_text_stream(
                    text=text,
                    role_id=request.role_id,
                    context=request.context,
                )
            async for chunk in chunks:
                data = json.dumps({"delta": chunk}, ensure_ascii=False)
                yield f"data: {data}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
        },
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

