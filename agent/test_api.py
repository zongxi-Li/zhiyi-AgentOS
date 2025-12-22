"""
Kinlin AI 服务测试脚本
用于测试所有API接口功能（无需真实API key，使用模拟响应）
"""
import requests
import json
import base64
from typing import Dict, Any

# 服务地址
BASE_URL = "http://localhost:8000"

def print_response(title: str, response: requests.Response):
    """打印响应结果"""
    print(f"\n{'='*60}")
    print(f"测试: {title}")
    print(f"{'='*60}")
    print(f"状态码: {response.status_code}")
    try:
        if response.headers.get('content-type', '').startswith('application/json'):
            print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        else:
            print(f"响应类型: {response.headers.get('content-type', 'unknown')}")
            print(f"响应长度: {len(response.content)} bytes")
    except Exception as e:
        print(f"响应解析错误: {e}")
        print(f"原始响应: {response.text[:500]}")

def test_health_check():
    """测试健康检查"""
    print("\n🔍 测试健康检查接口...")
    response = requests.get(f"{BASE_URL}/health")
    print_response("健康检查", response)
    return response.status_code == 200

def test_root():
    """测试根路径"""
    print("\n🔍 测试根路径...")
    response = requests.get(f"{BASE_URL}/")
    print_response("根路径", response)
    return response.status_code == 200

def test_text_chat():
    """测试文本对话"""
    print("\n💬 测试文本对话...")
    data = {
        "text": "你好，请介绍一下你自己",
        "role_id": None,
        "context": None
    }
    response = requests.post(
        f"{BASE_URL}/ai/chat/text",
        json=data,
        headers={"Content-Type": "application/json"}
    )
    print_response("文本对话", response)
    return response.status_code == 200

def test_text_chat_with_role():
    """测试带角色的文本对话"""
    print("\n💬 测试带角色的文本对话...")
    data = {
        "text": "请解释一下什么是机器学习",
        "role_id": "teacher",
        "context": None
    }
    response = requests.post(
        f"{BASE_URL}/ai/chat/text",
        json=data,
        headers={"Content-Type": "application/json"}
    )
    print_response("带角色的文本对话", response)
    return response.status_code == 200

def test_text_chat_with_context():
    """测试带上下文的文本对话"""
    print("\n💬 测试带上下文的文本对话...")
    data = {
        "text": "刚才我们聊了什么？",
        "role_id": None,
        "context": [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好！我是Kinlin AI助手，很高兴为您服务。"}
        ]
    }
    response = requests.post(
        f"{BASE_URL}/ai/chat/text",
        json=data,
        headers={"Content-Type": "application/json"}
    )
    print_response("带上下文的文本对话", response)
    return response.status_code == 200

def test_tts():
    """测试语音合成"""
    print("\n🔊 测试语音合成...")
    data = {
        "text": "这是语音合成测试",
        "voice": "default",
        "speed": 1.0,
        "pitch": 1.0
    }
    response = requests.post(
        f"{BASE_URL}/ai/tts",
        json=data,
        headers={"Content-Type": "application/json"}
    )
    print_response("语音合成", response)
    return response.status_code == 200

def test_tts_with_params():
    """测试带参数的语音合成"""
    print("\n🔊 测试带参数的语音合成...")
    data = {
        "text": "这是测试语速和音调的语音合成",
        "voice": "default",
        "speed": 1.2,
        "pitch": 1.1
    }
    response = requests.post(
        f"{BASE_URL}/ai/tts",
        json=data,
        headers={"Content-Type": "application/json"}
    )
    print_response("带参数的语音合成", response)
    return response.status_code == 200

def test_emotion_analysis():
    """测试情感分析"""
    print("\n😊 测试情感分析...")
    try:
        data = {
            "text": "我今天心情很好！",
            "audio_features": None,
            "facial_features": None
        }
        response = requests.post(
            f"{BASE_URL}/ai/emotion/analyze",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        print_response("情感分析", response)
        return response.status_code == 200
    except Exception as e:
        print(f"情感分析接口可能未实现: {e}")
        return False

def test_digital_human():
    """测试数字人功能"""
    print("\n👤 测试数字人功能...")
    try:
        data = {
            "role_id": "lawyer",
            "text": "你好，我是律师助手"
        }
        response = requests.post(
            f"{BASE_URL}/ai/digital-human/animate",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        print_response("数字人动画", response)
        return response.status_code == 200
    except Exception as e:
        print(f"数字人接口可能未实现: {e}")
        return False

def test_role_fusion():
    """测试角色融合"""
    print("\n🔀 测试角色融合...")
    try:
        data = {
            "question": "我想创业，需要法律和商业建议",
            "role_ids": ["lawyer", "teacher"],
            "weights": None
        }
        response = requests.post(
            f"{BASE_URL}/ai/role-fusion/fuse",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        print_response("角色融合", response)
        return response.status_code == 200
    except Exception as e:
        print(f"角色融合接口可能未实现: {e}")
        return False

def test_knowledge_graph():
    """测试知识图谱"""
    print("\n📊 测试知识图谱...")
    try:
        # 测试查询
        data = {
            "query": "什么是人工智能",
            "top_k": 5
        }
        response = requests.post(
            f"{BASE_URL}/ai/knowledge-graph/query",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        print_response("知识图谱查询", response)
        return response.status_code == 200
    except Exception as e:
        print(f"知识图谱接口可能未实现: {e}")
        return False

def test_rag():
    """测试RAG功能"""
    print("\n📚 测试RAG功能...")
    try:
        # 测试查询
        data = {
            "query": "测试查询",
            "top_k": 5
        }
        response = requests.post(
            f"{BASE_URL}/rag/query",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        print_response("RAG查询", response)
        return response.status_code == 200
    except Exception as e:
        print(f"RAG接口可能未实现: {e}")
        return False

def run_all_tests():
    """运行所有测试"""
    print("="*60)
    print("🚀 Kinlin AI 服务测试开始")
    print("="*60)
    print(f"测试服务地址: {BASE_URL}")
    print("注意: 当前使用模拟响应，无需真实API key")
    print("="*60)
    
    results = []
    
    # 基础测试
    results.append(("健康检查", test_health_check()))
    results.append(("根路径", test_root()))
    
    # 核心功能测试
    results.append(("文本对话", test_text_chat()))
    results.append(("带角色文本对话", test_text_chat_with_role()))
    results.append(("带上下文文本对话", test_text_chat_with_context()))
    results.append(("语音合成", test_tts()))
    results.append(("带参数语音合成", test_tts_with_params()))
    
    # 创新功能测试（可能未完全实现）
    results.append(("情感分析", test_emotion_analysis()))
    results.append(("数字人", test_digital_human()))
    results.append(("角色融合", test_role_fusion()))
    results.append(("知识图谱", test_knowledge_graph()))
    results.append(("RAG", test_rag()))
    
    # 汇总结果
    print("\n" + "="*60)
    print("📊 测试结果汇总")
    print("="*60)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    print("="*60)
    print(f"总计: {passed}/{total} 测试通过")
    print("="*60)
    
    if passed == total:
        print("🎉 所有测试通过！")
    elif passed > 0:
        print(f"⚠️  部分测试通过 ({passed}/{total})")
        print("提示: 某些创新功能可能未完全实现，这是正常的")
    else:
        print("❌ 所有测试失败，请检查服务是否正常运行")
    
    return passed, total

if __name__ == "__main__":
    try:
        run_all_tests()
    except requests.exceptions.ConnectionError:
        print("\n❌ 错误: 无法连接到服务")
        print("请确保服务已启动: python app/main.py")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

