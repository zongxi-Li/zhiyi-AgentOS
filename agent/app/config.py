"""
配置管理
"""
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "Kinlin AI Service"
    DEBUG: bool = False
    
    # 麒麟AI SDK配置
    KYLIN_AI_API_KEY: str = ""  # 默认空字符串，可通过环境变量或.env文件设置
    KYLIN_AI_ENDPOINT: str = "https://api.kylin.ai"
    KYLIN_AI_TIMEOUT: int = 30
    
    # 模型配置
    TEXT_MODEL_NAME: str = "default"
    ASR_MODEL_NAME: str = "default"
    TTS_MODEL_NAME: str = "default"
    
    # CORS配置
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8080"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()

