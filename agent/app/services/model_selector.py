"""
智能模型选择服务
根据性能、速度、资源等因素选择最优模型
"""
import logging
from typing import Dict, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class ModelType(Enum):
    """模型类型"""
    FAST = "fast"      # 快速模型
    BALANCED = "balanced"  # 平衡模型
    ADVANCED = "advanced"  # 高级模型

class ModelSelector:
    """模型选择器"""
    
    def __init__(self):
        self.models = {
            ModelType.FAST: {
                "name": "fast-model",
                "speed": 0.9,
                "quality": 0.6,
                "resource": 0.3
            },
            ModelType.BALANCED: {
                "name": "balanced-model",
                "speed": 0.7,
                "quality": 0.8,
                "resource": 0.6
            },
            ModelType.ADVANCED: {
                "name": "advanced-model",
                "speed": 0.4,
                "quality": 0.95,
                "resource": 0.9
            }
        }
    
    def select_model(
        self,
        priority: str = "balance",
        available_resources: float = 1.0
    ) -> ModelType:
        """
        选择模型
        
        Args:
            priority: 优先级 (speed/quality/balance)
            available_resources: 可用资源 (0.0-1.0)
        
        Returns:
            选择的模型类型
        """
        if priority == "speed":
            return ModelType.FAST
        elif priority == "quality":
            if available_resources > 0.7:
                return ModelType.ADVANCED
            else:
                return ModelType.BALANCED
        else:  # balance
            if available_resources > 0.5:
                return ModelType.BALANCED
            else:
                return ModelType.FAST
    
    def get_model_info(self, model_type: ModelType) -> Dict:
        """获取模型信息"""
        return self.models.get(model_type, {})

# 全局模型选择器实例
model_selector = ModelSelector()

