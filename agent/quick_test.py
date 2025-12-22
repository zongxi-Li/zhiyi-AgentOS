"""
快速测试脚本 - 最简单的测试方法
"""
import requests

BASE_URL = "http://localhost:8000"

print("🚀 快速测试 Kinlin AI 服务")
print("="*50)

# 测试1: 健康检查
print("\n1️⃣ 测试健康检查...")
try:
    r = requests.get(f"{BASE_URL}/health", timeout=5)
    print(f"   ✅ 状态码: {r.status_code}")
    print(f"   📄 响应: {r.json()}")
except Exception as e:
    print(f"   ❌ 错误: {e}")
    print("   💡 提示: 请确保服务已启动 (python app/main.py)")

# 测试2: 文本对话
print("\n2️⃣ 测试文本对话...")
try:
    r = requests.post(
        f"{BASE_URL}/ai/chat/text",
        json={"text": "你好"},
        timeout=10
    )
    print(f"   ✅ 状态码: {r.status_code}")
    data = r.json()
    print(f"   💬 AI回复: {data.get('text', 'N/A')}")
    print(f"   📊 置信度: {data.get('confidence', 0)}")
except Exception as e:
    print(f"   ❌ 错误: {e}")

# 测试3: 语音合成
print("\n3️⃣ 测试语音合成...")
try:
    r = requests.post(
        f"{BASE_URL}/ai/tts",
        json={"text": "这是测试", "speed": 1.0, "pitch": 1.0},
        timeout=10
    )
    print(f"   ✅ 状态码: {r.status_code}")
    print(f"   🔊 音频数据长度: {len(r.json().get('audio', b''))} bytes")
except Exception as e:
    print(f"   ❌ 错误: {e}")

print("\n" + "="*50)
print("✨ 测试完成！")
print("\n💡 提示:")
print("   - 如果看到 ✅，说明接口正常")
print("   - 当前使用模拟响应，无需真实API key")
print("   - 详细测试请运行: python test_api.py")

