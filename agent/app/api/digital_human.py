"""
数字人API路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
from app.services.digital_human_service import digital_human_service

router = APIRouter()


class CreateDigitalHumanRequest(BaseModel):
    role_id: str
    personality: Optional[str] = None
    profession: Optional[str] = None
    style: Optional[str] = "realistic"


class UpdateAnimationRequest(BaseModel):
    role_id: str
    audio: bytes
    text: str


class SwitchStyleRequest(BaseModel):
    role_id: str
    new_style: str  # realistic/cartoon/anime


@router.post("/digital-human/create")
async def create_digital_human(request: CreateDigitalHumanRequest):
    """创建数字人"""
    try:
        role_config = {
            "role_id": request.role_id,
            "personality": request.personality or "",
            "profession": request.profession or "",
            "style": request.style
        }
        avatar_data = digital_human_service.create_digital_human(role_config)
        return {"success": True, "data": avatar_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/digital-human/animation")
async def update_animation(request: UpdateAnimationRequest):
    """更新数字人动画"""
    try:
        animation = digital_human_service.update_digital_human_animation(
            role_id=request.role_id,
            audio=request.audio,
            text=request.text
        )
        return {"success": True, "data": animation}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/digital-human/style")
async def switch_style(request: SwitchStyleRequest):
    """切换数字人风格"""
    try:
        avatar_data = digital_human_service.switch_avatar_style(
            role_id=request.role_id,
            new_style=request.new_style
        )
        return {"success": True, "data": avatar_data}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


