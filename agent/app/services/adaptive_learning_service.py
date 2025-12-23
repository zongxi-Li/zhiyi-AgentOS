"""
自适应学习角色系统服务
基于用户反馈持续优化角色参数和对话风格
"""
import logging
from typing import Dict, List, Optional, Any
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


class AdaptiveLearningService:
    """自适应学习服务"""
    
    def __init__(self):
        self.role_feedback_history = defaultdict(list)  # 角色反馈历史
        self.role_parameters = {}  # 角色参数缓存
        
    def collect_feedback(
        self,
        role_id: str,
        conversation_id: str,
        feedback_type: str,
        feedback_value: float,
        user_id: Optional[str] = None,
        context: Optional[Dict] = None
    ):
        """
        收集用户反馈
        
        Args:
            role_id: 角色ID
            conversation_id: 对话ID
            feedback_type: 反馈类型 (quality/relevance/helpfulness/satisfaction)
            feedback_value: 反馈值 (0.0-1.0)
            user_id: 用户ID（可选）
            context: 上下文信息（可选）
        """
        feedback = {
            "role_id": role_id,
            "conversation_id": conversation_id,
            "feedback_type": feedback_type,
            "feedback_value": feedback_value,
            "user_id": user_id,
            "context": context or {},
            "timestamp": self._get_timestamp()
        }
        
        self.role_feedback_history[role_id].append(feedback)
        
        # 限制历史记录数量（保留最近1000条）
        if len(self.role_feedback_history[role_id]) > 1000:
            self.role_feedback_history[role_id] = self.role_feedback_history[role_id][-1000:]
        
        logger.info(f"收集反馈: {role_id}, {feedback_type}={feedback_value}")
        
        # 触发参数调整
        self._trigger_parameter_adjustment(role_id)
    
    def adjust_role_parameters(
        self,
        role_id: str,
        base_role_config: Dict
    ) -> Dict:
        """
        根据反馈调整角色参数
        
        Args:
            role_id: 角色ID
            base_role_config: 基础角色配置
        
        Returns:
            调整后的角色配置
        """
        if role_id not in self.role_feedback_history:
            return base_role_config
        
        feedbacks = self.role_feedback_history[role_id]
        if not feedbacks:
            return base_role_config
        
        # 分析反馈
        feedback_analysis = self._analyze_feedback(feedbacks)
        
        # 计算调整量
        adjustments = self._calculate_adjustments(feedback_analysis)
        
        # 应用调整
        adjusted_config = self._apply_adjustments(base_role_config, adjustments)
        
        # 缓存调整后的参数
        self.role_parameters[role_id] = adjusted_config
        
        logger.info(f"角色参数已调整: {role_id}, 调整项: {list(adjustments.keys())}")
        
        return adjusted_config
    
    def _analyze_feedback(self, feedbacks: List[Dict]) -> Dict:
        """分析反馈数据"""
        if not feedbacks:
            return {}
        
        # 按反馈类型分组
        feedback_by_type = defaultdict(list)
        for feedback in feedbacks:
            feedback_type = feedback["feedback_type"]
            feedback_by_type[feedback_type].append(feedback["feedback_value"])
        
        # 计算平均分和趋势
        analysis = {}
        for feedback_type, values in feedback_by_type.items():
            recent_values = values[-50:] if len(values) > 50 else values  # 最近50条
            older_values = values[:-50] if len(values) > 50 else []
            
            analysis[feedback_type] = {
                "average": sum(values) / len(values) if values else 0.5,
                "recent_average": sum(recent_values) / len(recent_values) if recent_values else 0.5,
                "trend": self._calculate_trend(recent_values, older_values),
                "count": len(values)
            }
        
        return analysis
    
    def _calculate_trend(self, recent: List[float], older: List[float]) -> str:
        """计算反馈趋势"""
        if not recent:
            return "stable"
        
        recent_avg = sum(recent) / len(recent)
        
        if not older:
            return "stable"
        
        older_avg = sum(older) / len(older)
        
        diff = recent_avg - older_avg
        
        if diff > 0.1:
            return "improving"
        elif diff < -0.1:
            return "declining"
        else:
            return "stable"
    
    def _calculate_adjustments(self, feedback_analysis: Dict) -> Dict:
        """根据反馈分析计算调整量"""
        adjustments = {}
        
        # 质量反馈调整
        if "quality" in feedback_analysis:
            quality = feedback_analysis["quality"]
            if quality["average"] < 0.6:
                adjustments["response_length"] = +0.2  # 增加回复长度
                adjustments["detail_level"] = +0.3  # 增加详细程度
            elif quality["average"] > 0.8:
                adjustments["response_length"] = -0.1  # 适度减少长度
                adjustments["detail_level"] = -0.1
        
        # 相关性反馈调整
        if "relevance" in feedback_analysis:
            relevance = feedback_analysis["relevance"]
            if relevance["average"] < 0.6:
                adjustments["context_awareness"] = +0.3  # 增强上下文理解
                adjustments["topic_focus"] = +0.2  # 增强主题聚焦
        
        # 有用性反馈调整
        if "helpfulness" in feedback_analysis:
            helpfulness = feedback_analysis["helpfulness"]
            if helpfulness["average"] < 0.6:
                adjustments["actionability"] = +0.3  # 增加可操作性
                adjustments["example_usage"] = +0.2  # 增加示例
        
        # 满意度反馈调整
        if "satisfaction" in feedback_analysis:
            satisfaction = feedback_analysis["satisfaction"]
            if satisfaction["trend"] == "declining":
                adjustments["warmth"] = +0.2  # 增加温暖度
                adjustments["patience"] = +0.2  # 增加耐心
            elif satisfaction["trend"] == "improving":
                # 保持当前风格
                pass
        
        return adjustments
    
    def _apply_adjustments(self, base_config: Dict, adjustments: Dict) -> Dict:
        """应用调整到角色配置"""
        adjusted_config = base_config.copy()
        
        for key, value in adjustments.items():
            if key in adjusted_config:
                if isinstance(adjusted_config[key], (int, float)):
                    # 数值调整
                    adjusted_config[key] = max(0.0, min(1.0, adjusted_config[key] + value))
                elif isinstance(adjusted_config[key], bool):
                    # 布尔值调整
                    adjusted_config[key] = value > 0
            else:
                # 新增参数
                adjusted_config[key] = max(0.0, min(1.0, value))
        
        return adjusted_config
    
    def get_learning_statistics(self, role_id: str) -> Dict:
        """获取学习统计信息"""
        if role_id not in self.role_feedback_history:
            return {
                "total_feedbacks": 0,
                "average_scores": {},
                "trends": {},
                "adjustments_applied": False
            }
        
        feedbacks = self.role_feedback_history[role_id]
        analysis = self._analyze_feedback(feedbacks)
        
        return {
            "total_feedbacks": len(feedbacks),
            "average_scores": {
                k: v["average"] for k, v in analysis.items()
            },
            "trends": {
                k: v["trend"] for k, v in analysis.items()
            },
            "adjustments_applied": role_id in self.role_parameters,
            "recent_feedback_count": len([f for f in feedbacks if self._is_recent(f)])
        }
    
    def _is_recent(self, feedback: Dict, days: int = 7) -> bool:
        """判断反馈是否在最近N天内"""
        # 简化实现：假设反馈按时间顺序添加
        return True
    
    def _get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def reset_role_learning(self, role_id: str):
        """重置角色的学习数据"""
        if role_id in self.role_feedback_history:
            del self.role_feedback_history[role_id]
        if role_id in self.role_parameters:
            del self.role_parameters[role_id]
        logger.info(f"已重置角色学习数据: {role_id}")


# 全局自适应学习服务实例
adaptive_learning_service = AdaptiveLearningService()


