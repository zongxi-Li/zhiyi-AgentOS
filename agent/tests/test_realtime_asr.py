"""
实时语音识别服务单元测试
"""
import pytest
import asyncio
from app.services.realtime_asr_service import RealtimeASRService


class TestRealtimeASRService:
    """实时语音识别服务测试"""
    
    @pytest.fixture
    def service(self):
        """创建服务实例"""
        return RealtimeASRService()
    
    @pytest.mark.asyncio
    async def test_start_recognition_session(self, service):
        """测试开始识别会话"""
        session_id = "test_session_1"
        await service.start_recognition_session(
            session_id=session_id,
            language="zh-CN",
            sample_rate=16000
        )
        
        assert session_id in service.active_sessions
        assert service.active_sessions[session_id]["status"] == "active"
        assert service.active_sessions[session_id]["language"] == "zh-CN"
        assert service.active_sessions[session_id]["sample_rate"] == 16000
    
    @pytest.mark.asyncio
    async def test_process_audio_chunk(self, service):
        """测试处理音频块"""
        session_id = "test_session_2"
        await service.start_recognition_session(session_id)
        
        # 模拟音频数据
        audio_chunk = b'\x00' * 1600  # 100ms的音频数据（16kHz采样率）
        
        result = await service.process_audio_chunk(session_id, audio_chunk)
        
        assert result["session_id"] == session_id
        assert "partial_text" in result or "final_text" in result
        assert "is_final" in result
        assert "confidence" in result
    
    @pytest.mark.asyncio
    async def test_end_recognition_session(self, service):
        """测试结束识别会话"""
        session_id = "test_session_3"
        await service.start_recognition_session(session_id)
        
        result = await service.end_recognition_session(session_id)
        
        assert result["session_id"] == session_id
        assert "final_text" in result
        assert "all_results" in result
        assert session_id not in service.active_sessions
    
    def test_filter_noise(self, service):
        """测试噪音过滤"""
        # 模拟音频数据
        audio_data = b'\x00' * 1600
        
        filtered = service._filter_noise(audio_data, 16000)
        
        assert isinstance(filtered, bytes)
        assert len(filtered) == len(audio_data)
    
    def test_calculate_energy(self, service):
        """测试计算音频能量"""
        # 模拟音频数据
        audio_data = b'\x00' * 1600
        
        energy = service._calculate_energy(audio_data)
        
        assert isinstance(energy, float)
        assert 0.0 <= energy <= 1.0
    
    @pytest.mark.asyncio
    async def test_multiple_sessions(self, service):
        """测试多个会话同时存在"""
        session1 = "session_1"
        session2 = "session_2"
        
        await service.start_recognition_session(session1)
        await service.start_recognition_session(session2)
        
        assert len(service.active_sessions) == 2
        assert session1 in service.active_sessions
        assert session2 in service.active_sessions
        
        await service.end_recognition_session(session1)
        assert session1 not in service.active_sessions
        assert session2 in service.active_sessions


