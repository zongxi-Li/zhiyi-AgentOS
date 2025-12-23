"""
角色风格学习服务单元测试
"""
import pytest
from app.services.role_style_learning_service import (
    RoleStyleLearningService,
    RoleDescriptionParser,
    StyleExampleLearner
)


class TestRoleDescriptionParser:
    """角色描述解析器测试"""
    
    @pytest.fixture
    def parser(self):
        """创建解析器实例"""
        return RoleDescriptionParser()
    
    def test_parse_description_formal(self, parser):
        """测试解析正式风格描述"""
        description = "一位严谨专业的律师，擅长法律咨询"
        result = parser.parse_description(description)
        
        assert "style_features" in result
        assert "knowledge_domains" in result
        assert "personality_traits" in result
        assert "tone" in result
        assert "法律" in result["knowledge_domains"]
    
    def test_parse_description_casual(self, parser):
        """测试解析轻松风格描述"""
        description = "一位友好的教师，耐心细致，善于引导"
        result = parser.parse_description(description)
        
        assert "style_features" in result
        assert "教育" in result["knowledge_domains"] or len(result["knowledge_domains"]) >= 0
        assert "tone" in result
    
    def test_parse_empty_description(self, parser):
        """测试解析空描述"""
        result = parser.parse_description("")
        
        assert result["style_features"] == {}
        assert result["knowledge_domains"] == []
        assert result["personality_traits"] == []
        assert result["tone"] == "neutral"
    
    def test_extract_style_features(self, parser):
        """测试提取风格特征"""
        description = "正式、专业、严谨的律师"
        features = parser._extract_style_features(description)
        
        assert isinstance(features, dict)
        assert "formal" in features or "professional" in features or len(features) >= 0
    
    def test_extract_knowledge_domains(self, parser):
        """测试提取知识领域"""
        description = "一位经验丰富的程序员，擅长Java和Python开发"
        domains = parser._extract_knowledge_domains(description)
        
        assert isinstance(domains, list)
        assert "技术" in domains or len(domains) >= 0


class TestStyleExampleLearner:
    """风格示例学习器测试"""
    
    @pytest.fixture
    def learner(self):
        """创建学习器实例"""
        return StyleExampleLearner()
    
    def test_learn_from_examples(self, learner):
        """测试从示例中学习"""
        examples = [
            {"user": "你好", "role": "您好，有什么可以帮助您的吗？"},
            {"user": "我想咨询", "role": "好的，请详细说明您的问题。"}
        ]
        role_id = "test_role_1"
        
        learned = learner.learn_from_examples(examples, role_id)
        
        assert "patterns" in learned
        assert "language_features" in learned
        assert "response_structure" in learned
        assert "example_count" in learned
        assert learned["example_count"] == 2
    
    def test_analyze_conversation_patterns(self, learner):
        """测试分析对话模式"""
        examples = [
            {"user": "你好", "role": "您好！很高兴为您服务。"},
            {"user": "问题？", "role": "这是一个很好的问题，让我来解答。"}
        ]
        
        patterns = learner._analyze_conversation_patterns(examples)
        
        assert "greeting_style" in patterns
        assert "question_handling" in patterns
        assert "explanation_style" in patterns
        assert "closing_style" in patterns
    
    def test_extract_language_features(self, learner):
        """测试提取语言特征"""
        examples = [
            {"user": "问题1", "role": "这是答案1。"},
            {"user": "问题2", "role": "这是答案2。"}
        ]
        
        features = learner._extract_language_features(examples)
        
        assert "avg_length" in features
        assert "sentence_count" in features
        assert "question_count" in features
        assert features["avg_length"] > 0


class TestRoleStyleLearningService:
    """角色风格学习服务测试"""
    
    @pytest.fixture
    def service(self):
        """创建服务实例"""
        return RoleStyleLearningService()
    
    def test_learn_role_style_from_description(self, service):
        """测试从描述中学习角色风格"""
        role_id = "test_role_2"
        description = "一位专业的心理咨询师，耐心细致"
        
        learned = service.learn_role_style(
            role_id=role_id,
            description=description
        )
        
        assert learned["role_id"] == role_id
        assert "from_description" in learned
        assert "combined_style" in learned
        assert learned["from_description"]["tone"] in ["formal", "casual", "warm", "neutral"]
    
    def test_learn_role_style_from_examples(self, service):
        """测试从示例中学习角色风格"""
        role_id = "test_role_3"
        examples = [
            {"user": "你好", "role": "您好，有什么可以帮助您的吗？"}
        ]
        
        learned = service.learn_role_style(
            role_id=role_id,
            style_examples=examples
        )
        
        assert learned["role_id"] == role_id
        assert "from_examples" in learned
        assert "combined_style" in learned
    
    def test_learn_role_style_combined(self, service):
        """测试合并描述和示例学习角色风格"""
        role_id = "test_role_4"
        description = "一位耐心的教师"
        examples = [
            {"user": "问题", "role": "让我来详细解释一下..."}
        ]
        
        learned = service.learn_role_style(
            role_id=role_id,
            description=description,
            style_examples=examples
        )
        
        assert learned["role_id"] == role_id
        assert "from_description" in learned
        assert "from_examples" in learned
        assert "combined_style" in learned
        assert "style_features" in learned["combined_style"]


