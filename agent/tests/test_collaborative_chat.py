"""
协作对话服务单元测试
"""
import pytest
import asyncio
from app.services.collaborative_chat_service import CollaborativeChatService
from app.services.ai_service import AIService


class TestCollaborativeChatService:
    """协作对话服务测试"""
    
    @pytest.fixture
    def service(self):
        """创建服务实例"""
        return CollaborativeChatService()
    
    @pytest.fixture
    def mock_ai_service(self):
        """创建模拟AI服务"""
        class MockAIService:
            async def generate_text(self, text, role_id=None, context=None):
                return {
                    "text": f"回复: {text}",
                    "confidence": 0.9
                }
        return MockAIService()
    
    def test_create_session(self, service):
        """测试创建会话"""
        role_id = "lawyer"
        creator_id = "user_1"
        
        session_id = service.create_session(role_id, creator_id)
        
        assert session_id is not None
        assert session_id in service.active_sessions
        session = service.active_sessions[session_id]
        assert session.role_id == role_id
        assert creator_id in session.participants
    
    def test_join_session(self, service):
        """测试加入会话"""
        role_id = "teacher"
        creator_id = "user_1"
        session_id = service.create_session(role_id, creator_id)
        
        user_2 = "user_2"
        success = service.join_session(session_id, user_2)
        
        assert success is True
        session = service.active_sessions[session_id]
        assert user_2 in session.participants
        assert len(session.participants) == 2
    
    def test_leave_session(self, service):
        """测试离开会话"""
        role_id = "programmer"
        creator_id = "user_1"
        session_id = service.create_session(role_id, creator_id)
        
        service.leave_session(session_id, creator_id)
        
        assert session_id not in service.active_sessions
    
    @pytest.mark.asyncio
    async def test_process_message(self, service, mock_ai_service):
        """测试处理消息"""
        role_id = "writer"
        creator_id = "user_1"
        session_id = service.create_session(role_id, creator_id)
        
        result = await service.process_message(
            session_id=session_id,
            user_id=creator_id,
            content="测试消息",
            ai_service=mock_ai_service
        )
        
        assert result["session_id"] == session_id
        assert "response" in result
        assert "participants" in result
        assert "message_count" in result
    
    @pytest.mark.asyncio
    async def test_process_message_not_in_session(self, service, mock_ai_service):
        """测试不在会话中的用户发送消息"""
        role_id = "lawyer"
        creator_id = "user_1"
        session_id = service.create_session(role_id, creator_id)
        
        with pytest.raises(ValueError, match="不在会话中"):
            await service.process_message(
                session_id=session_id,
                user_id="user_2",  # 未加入会话
                content="测试消息",
                ai_service=mock_ai_service
            )
    
    def test_get_session_info(self, service):
        """测试获取会话信息"""
        role_id = "teacher"
        creator_id = "user_1"
        session_id = service.create_session(role_id, creator_id)
        
        info = service.get_session_info(session_id)
        
        assert info is not None
        assert info["session_id"] == session_id
        assert info["role_id"] == role_id
        assert info["participant_count"] == 1
        assert creator_id in info["participants"]
    
    def test_get_user_sessions(self, service):
        """测试获取用户会话"""
        user_id = "user_1"
        session1 = service.create_session("role_1", user_id)
        session2 = service.create_session("role_2", user_id)
        
        sessions = service.get_user_sessions(user_id)
        
        assert len(sessions) == 2
        session_ids = [s["session_id"] for s in sessions]
        assert session1 in session_ids
        assert session2 in session_ids
    
    def test_cleanup_inactive_sessions(self, service):
        """测试清理不活跃会话"""
        role_id = "test_role"
        creator_id = "user_1"
        session_id = service.create_session(role_id, creator_id)
        
        # 模拟不活跃会话（修改最后活动时间）
        session = service.active_sessions[session_id]
        from datetime import datetime, timedelta
        session.last_activity = datetime.now() - timedelta(hours=25)
        
        cleaned_count = service.cleanup_inactive_sessions(hours=24)
        
        assert cleaned_count >= 0
        # 会话应该被清理
        assert session_id not in service.active_sessions or cleaned_count > 0


