"""
对话API路由
"""
from fastapi import APIRouter, UploadFile, File, Form, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import json
import asyncio
import logging
from app.services.aiservice import AIService
from app.config import settings
from app.ai_engine.kylin_sdk.client import KylinAIClient
from app.ai_engine.model_runtime import (
    apply_reasoning_instruction,
    list_system_runtime_models,
    resolve_system_runtime_config,
    stream_with_runtime_model,
)

router = APIRouter()

# 依赖注入AI服务
ai_service = AIService()
stream_client = KylinAIClient()
logger = logging.getLogger(__name__)

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


@router.get("/chat/models")
async def chat_models():
    """Return models available through the server-managed API connection."""
    return await list_system_runtime_models()

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

async def _stream_sse_events(chunks, http_request: Request, heartbeat_interval: float):
    """Forward model chunks while emitting comments and promptly cancelling the iterator."""
    iterator = chunks.__aiter__()
    pending_chunk = None
    try:
        while True:
            if await http_request.is_disconnected():
                logger.info("SSE client disconnected before next model chunk")
                return

            pending_chunk = asyncio.create_task(iterator.__anext__())
            while not pending_chunk.done():
                done, _ = await asyncio.wait({pending_chunk}, timeout=heartbeat_interval)
                if pending_chunk in done:
                    break
                if await http_request.is_disconnected():
                    logger.info("SSE client disconnected while awaiting model chunk")
                    return
                yield ": heartbeat\n\n"

            try:
                chunk = pending_chunk.result()
            except StopAsyncIteration:
                yield "data: [DONE]\n\n"
                return

            data = json.dumps({"delta": chunk}, ensure_ascii=False)
            yield f"data: {data}\n\n"
            pending_chunk = None
    except asyncio.CancelledError:
        logger.info("SSE generation cancelled by downstream")
        raise
    except Exception as error:
        logger.exception("SSE model stream failed. type=%s", type(error).__name__)
        yield 'event: error\ndata: {"error":"AI_STREAM_FAILED"}\n\n'
    finally:
        if pending_chunk is not None and not pending_chunk.done():
            pending_chunk.cancel()
            await asyncio.gather(pending_chunk, return_exceptions=True)
        close = getattr(iterator, "aclose", None)
        if close is not None:
            await close()


@router.post("/chat/text/stream")
async def chat_text_stream(chat_request: ChatRequest, http_request: Request):
    """流式文本对话 (SSE)"""
    async def event_stream():
        if chat_request.model and not chat_request.base_url and not chat_request.api_key:
            chat_request.model, chat_request.base_url, chat_request.api_key = resolve_system_runtime_config(chat_request.model)

        if chat_request.model or chat_request.base_url or chat_request.api_key:
            chunks = stream_with_runtime_model(
                text=chat_request.text,
                context=chat_request.context,
                model=chat_request.model or "",
                base_url=chat_request.base_url or "",
                api_key=chat_request.api_key or "",
                reasoning_effort=chat_request.reasoning_effort,
            )
        else:
            text = chat_request.text
            if chat_request.reasoning_effort != "off":
                messages = apply_reasoning_instruction(
                    [{"role": "user", "content": text}], chat_request.reasoning_effort
                )
                text = "\n".join(item["content"] for item in messages)
            chunks = stream_client.generate_text_stream(
                text=text,
                role_id=chat_request.role_id,
                context=chat_request.context,
            )
        async for event in _stream_sse_events(
                chunks, http_request, max(settings.SSE_HEARTBEAT_INTERVAL, 0.1)):
            yield event
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

