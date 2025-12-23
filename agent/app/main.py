"""
Kinlin AI - Python AI服务主程序
提供AI能力：文本生成、语音识别、语音合成
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

from fastapi.exceptions import RequestValidationError
from app.api import chat, tts
from app.services.ai_service import AIService
from app.config import settings
from app.utils.logger import setup_logger
from app.middleware.error_handler import (
    validation_exception_handler,
    general_exception_handler
)

# 设置日志
logger = setup_logger()

# 生命周期事件处理器（替代已弃用的on_event）
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("Kinlin AI Service starting up...")
    logger.info(f"Kylin AI Endpoint: {settings.KYLIN_AI_ENDPOINT}")
    yield
    # 关闭时执行
    logger.info("Kinlin AI Service shutting down...")

app = FastAPI(
    title="Kinlin AI Service",
    description="Kinlin AI Python AI Service",
    version="1.0.0",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册异常处理器
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# 初始化AI服务
ai_service = AIService()

# 注册路由
app.include_router(chat.router, prefix="/ai", tags=["AI"])
app.include_router(tts.router, prefix="/ai", tags=["TTS"])

# 创新功能路由
try:
    from app.api import digital_human, emotion, role_fusion, knowledge_graph, adaptive_learning, multimodal, aigc, model_selector, performance, realtime_asr, role_style_learning, collaborative_chat, emotion_driven, federated_digital_human, digital_human_model_selector, kylin_os, rag_enhanced, communication_optimizer, performance_optimizer
    app.include_router(digital_human.router, prefix="/ai", tags=["DigitalHuman"])
    app.include_router(emotion.router, prefix="/ai", tags=["Emotion"])
    app.include_router(role_fusion.router, prefix="/ai", tags=["RoleFusion"])
    app.include_router(knowledge_graph.router, prefix="/ai", tags=["KnowledgeGraph"])
    app.include_router(adaptive_learning.router, prefix="/ai", tags=["AdaptiveLearning"])
    app.include_router(multimodal.router, prefix="/ai", tags=["Multimodal"])
    app.include_router(aigc.router, prefix="/ai", tags=["AIGC"])
    app.include_router(model_selector.router, prefix="/ai", tags=["ModelSelector"])
    app.include_router(performance.router, prefix="/performance", tags=["Performance"])
    app.include_router(realtime_asr.router, prefix="/ai", tags=["RealtimeASR"])
    app.include_router(role_style_learning.router, prefix="/ai", tags=["RoleStyleLearning"])
    app.include_router(collaborative_chat.router, prefix="/ai", tags=["CollaborativeChat"])
    app.include_router(emotion_driven.router, prefix="/ai", tags=["EmotionDriven"])
    app.include_router(federated_digital_human.router, prefix="/ai", tags=["FederatedDigitalHuman"])
    app.include_router(digital_human_model_selector.router, prefix="/ai", tags=["DigitalHumanModelSelector"])
    app.include_router(kylin_os.router, prefix="/ai", tags=["KylinOS"])
    app.include_router(rag_enhanced.router, prefix="/ai", tags=["RAGEnhanced"])
    app.include_router(communication_optimizer.router, prefix="/ai", tags=["CommunicationOptimizer"])
    app.include_router(performance_optimizer.router, prefix="/ai", tags=["PerformanceOptimizer"])
    logger.info("所有创新功能路由已加载")
except ImportError as e:
    logger.warning(f"部分创新功能路由未加载: {e}")

# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "Kinlin AI Agent",
        "version": "1.0.0"
    }

# RAG路由（待完善）
try:
    from app.api import rag
    app.include_router(rag.router, prefix="/rag", tags=["RAG"])
except ImportError:
    logger.warning("RAG模块未实现，跳过注册")

@app.get("/")
async def root():
    return {"message": "Kinlin AI Service", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

