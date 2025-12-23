"""
AIGC内容生成API路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
from app.services.aigc_service import aigc_service

router = APIRouter()


class TextGenerationRequest(BaseModel):
    prompt: str
    style: str = "default"  # default/creative/professional/casual
    length: str = "medium"  # short/medium/long
    role_context: Optional[Dict] = None


class ImageGenerationRequest(BaseModel):
    prompt: str
    style: str = "realistic"  # realistic/anime/cartoon/artistic
    size: str = "512x512"
    aspect_ratio: str = "1:1"


class VideoGenerationRequest(BaseModel):
    prompt: str
    duration: int = 10
    fps: int = 24
    style: str = "default"


class MultimodalGenerationRequest(BaseModel):
    text: Optional[Dict] = None  # {enabled, prompt, style, length}
    image: Optional[Dict] = None  # {enabled, prompt, style, size, aspect_ratio}
    video: Optional[Dict] = None  # {enabled, prompt, duration, fps, style}
    role_context: Optional[Dict] = None


@router.post("/aigc/text")
async def generate_text(request: TextGenerationRequest):
    """
    生成文字内容
    
    示例：
    {
        "prompt": "写一篇关于春天的散文",
        "style": "creative",
        "length": "medium"
    }
    """
    try:
        result = aigc_service.text_generator.generate_text(
            prompt=request.prompt,
            style=request.style,
            length=request.length,
            role_context=request.role_context
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文字生成失败: {str(e)}")


@router.post("/aigc/image")
async def generate_image(request: ImageGenerationRequest):
    """
    生成图像
    
    示例：
    {
        "prompt": "一幅春天的风景画",
        "style": "artistic",
        "size": "1024x1024"
    }
    """
    try:
        result = aigc_service.image_generator.generate_image(
            prompt=request.prompt,
            style=request.style,
            size=request.size,
            aspect_ratio=request.aspect_ratio
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图像生成失败: {str(e)}")


@router.post("/aigc/video")
async def generate_video(request: VideoGenerationRequest):
    """
    生成视频
    
    示例：
    {
        "prompt": "一个春天的动画场景",
        "duration": 15,
        "fps": 24
    }
    """
    try:
        result = aigc_service.video_generator.generate_video(
            prompt=request.prompt,
            duration=request.duration,
            fps=request.fps,
            style=request.style
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"视频生成失败: {str(e)}")


@router.post("/aigc/multimodal")
async def generate_multimodal(request: MultimodalGenerationRequest):
    """
    生成多模态内容
    
    示例：
    {
        "text": {
            "enabled": true,
            "prompt": "写一篇关于春天的文章",
            "style": "creative"
        },
        "image": {
            "enabled": true,
            "prompt": "春天的风景",
            "style": "artistic"
        },
        "video": {
            "enabled": false
        }
    }
    """
    try:
        request_dict = {
            "text": request.text or {},
            "image": request.image or {},
            "video": request.video or {}
        }
        
        result = aigc_service.generate_multimodal_content(
            request=request_dict,
            role_context=request.role_context
        )
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"多模态生成失败: {str(e)}")


@router.post("/aigc/presentation")
async def create_presentation(
    text_content: str,
    images: List[Dict],
    narration: bool = True
):
    """
    创建演示内容（数字人展示）
    
    示例：
    {
        "text_content": "这是演示的文字内容...",
        "images": [
            {"image_url": "image1.png"},
            {"image_url": "image2.png"}
        ],
        "narration": true
    }
    """
    try:
        result = aigc_service.create_presentation(
            text_content=text_content,
            images=images,
            narration=narration
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建演示失败: {str(e)}")


