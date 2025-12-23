"""
端到端测试场景
测试完整的用户交互流程
"""
import pytest
import asyncio
from app.services.ai_service import AIService
from app.services.emotion_driven_response import emotion_driven_response_service
from app.services.collaborative_chat_service import collaborative_chat_service
from app.services.role_style_learning_service import role_style_learning_service


class TestE2EScenarios:
    """端到端测试场景"""
    
    @pytest.fixture
    def ai_service(self):
        """创建AI服务实例"""
        return AIService()
    
    @pytest.mark.asyncio
    async def test_complete_chat_flow(self, ai_service):
        """测试完整对话流程"""
        # 1. 用户发送消息
        user_message = "你好，我想咨询一个问题"
        role_id = "lawyer"
        
        # 2. AI生成回复
        response = await ai_service.generate_text(
            text=user_message,
            role_id=role_id
        )
        
        # 验证
        assert response is not None
        assert "text" in response
        assert len(response["text"]) > 0
    
    @pytest.mark.asyncio
    async def test_emotion_driven_conversation(self):
        """测试情感驱动对话流程"""
        # 1. 用户发送带情感的消息
        question = "我最近很焦虑，不知道该怎么办"
        role_config = {
            "role_id": "counselor",
            "personality": {"warmth": 0.8, "patience": 0.9}
        }
        
        # 2. 生成情感驱动回复
        response = await emotion_driven_response_service.generate_response(
            question=question,
            role_config=role_config,
            text=question
        )
        
        # 验证
        assert response is not None
        assert "text" in response
        assert "emotion" in response
        assert "user_emotion" in response
    
    @pytest.mark.asyncio
    async def test_collaborative_chat_flow(self):
        """测试协作对话流程"""
        # 1. 创建协作会话
        role_id = "teacher"
        creator_id = "user_1"
        session_id = collaborative_chat_service.create_session(role_id, creator_id)
        
        # 2. 用户2加入会话
        user_2 = "user_2"
        success = collaborative_chat_service.join_session(session_id, user_2)
        assert success is True
        
        # 3. 用户1发送消息
        class MockAIService:
            async def generate_text(self, text, role_id=None, context=None):
                return {"text": f"回复: {text}"}
        
        mock_ai = MockAIService()
        result = await collaborative_chat_service.process_message(
            session_id=session_id,
            user_id=creator_id,
            content="第一个问题",
            ai_service=mock_ai
        )
        
        # 验证
        assert result["session_id"] == session_id
        assert "response" in result
        assert len(result["participants"]) == 2
    
    @pytest.mark.asyncio
    async def test_role_style_learning_flow(self):
        """测试角色风格学习流程"""
        # 1. 提供角色描述和示例
        role_id = "custom_role_1"
        description = "一位耐心的心理咨询师"
        examples = [
            {"user": "我很难过", "role": "我理解你的感受，能详细说说吗？"},
            {"user": "我不知道怎么办", "role": "没关系，我们一起慢慢分析。"}
        ]
        
        # 2. 学习角色风格
        learned = role_style_learning_service.learn_role_style(
            role_id=role_id,
            description=description,
            style_examples=examples
        )
        
        # 验证
        assert learned["role_id"] == role_id
        assert "from_description" in learned
        assert "from_examples" in learned
        assert "combined_style" in learned
    
    @pytest.mark.asyncio
    async def test_multi_turn_conversation(self, ai_service):
        """测试多轮对话流程"""
        context = []
        role_id = "programmer"
        
        # 第一轮
        message1 = "如何学习Python？"
        response1 = await ai_service.generate_text(
            text=message1,
            role_id=role_id,
            context=context
        )
        context.append({"role": "user", "content": message1})
        context.append({"role": "assistant", "content": response1["text"]})
        
        # 第二轮（带上下文）
        message2 = "有什么好的学习资源吗？"
        response2 = await ai_service.generate_text(
            text=message2,
            role_id=role_id,
            context=context
        )
        
        # 验证
        assert response1 is not None
        assert response2 is not None
        assert len(context) == 2  # 两轮对话的上下文


