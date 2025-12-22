# Kinlin AI 服务测试指南

## 📋 测试方法

### 方法1: 使用Python测试脚本（推荐）

运行测试脚本，自动测试所有接口：

```bash
cd E:\Project\Kinlin_AI\agent
.venv\Scripts\python.exe test_api.py
```

### 方法2: 使用curl命令测试

#### 1. 健康检查
```bash
curl http://localhost:8000/health
```

#### 2. 文本对话
```bash
curl -X POST http://localhost:8000/ai/chat/text \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"你好，请介绍一下你自己\"}"
```

#### 3. 带角色的文本对话
```bash
curl -X POST http://localhost:8000/ai/chat/text \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"请解释一下什么是机器学习\", \"role_id\": \"teacher\"}"
```

#### 4. 语音合成
```bash
curl -X POST http://localhost:8000/ai/tts \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"这是语音合成测试\", \"voice\": \"default\", \"speed\": 1.0, \"pitch\": 1.0}"
```

### 方法3: 使用浏览器测试

1. **健康检查**: 打开浏览器访问 `http://localhost:8000/health`
2. **API文档**: 访问 `http://localhost:8000/docs` 查看Swagger文档（如果已配置）
3. **根路径**: 访问 `http://localhost:8000/` 查看服务信息

### 方法4: 使用Postman或类似工具

1. 导入API集合（如果有）
2. 设置基础URL: `http://localhost:8000`
3. 测试各个接口

## 🧪 测试场景

### 基础功能测试

#### 1. 文本对话测试
- ✅ 简单对话
- ✅ 带角色对话
- ✅ 多轮对话（带上下文）
- ✅ 长文本处理

#### 2. 语音功能测试
- ✅ 语音合成（默认参数）
- ✅ 语音合成（自定义语速）
- ✅ 语音合成（自定义音调）
- ✅ 语音合成（组合参数）

### 创新功能测试

#### 1. 情感分析
```bash
curl -X POST http://localhost:8000/ai/emotion/analyze \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"我今天心情很好！\"}"
```

#### 2. 数字人
```bash
curl -X POST http://localhost:8000/ai/digital-human/animate \
  -H "Content-Type: application/json" \
  -d "{\"role_id\": \"lawyer\", \"text\": \"你好，我是律师助手\"}"
```

#### 3. 角色融合
```bash
curl -X POST http://localhost:8000/ai/role-fusion/fuse \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"我想创业，需要法律和商业建议\", \"role_ids\": [\"lawyer\", \"teacher\"]}"
```

#### 4. 知识图谱
```bash
curl -X POST http://localhost:8000/ai/knowledge-graph/query \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"什么是人工智能\", \"top_k\": 5}"
```

#### 5. RAG检索
```bash
curl -X POST http://localhost:8000/rag/query \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"测试查询\", \"top_k\": 5}"
```

## 📊 预期结果

### 成功响应示例

#### 文本对话响应
```json
{
  "text": "这是对'你好，请介绍一下你自己'的AI回复（模拟）",
  "confidence": 0.95,
  "tokens_used": 150
}
```

#### 健康检查响应
```json
{
  "status": "healthy",
  "service": "kinlin-ai-service"
}
```

## ⚠️ 注意事项

1. **模拟响应**: 当前使用模拟响应，返回的是示例数据
2. **API Key**: 开发环境无需API key，生产环境需要配置
3. **服务状态**: 确保服务已启动（`python app/main.py`）
4. **端口占用**: 确保8000端口未被占用

## 🔍 故障排查

### 问题1: 连接失败
```
ConnectionError: 无法连接到服务
```
**解决方案**: 检查服务是否启动，端口是否正确

### 问题2: 404错误
```
404 Not Found
```
**解决方案**: 检查URL路径是否正确，路由是否已注册

### 问题3: 500错误
```
500 Internal Server Error
```
**解决方案**: 查看服务日志，检查错误信息

## 📝 测试检查清单

- [ ] 服务启动成功
- [ ] 健康检查通过
- [ ] 文本对话功能正常
- [ ] 语音合成功能正常
- [ ] 创新功能接口可访问（可能返回模拟数据）
- [ ] 错误处理正常
- [ ] 日志记录正常

## 🚀 快速测试命令

```bash
# 1. 启动服务
cd E:\Project\Kinlin_AI\agent
.venv\Scripts\python.exe app\main.py

# 2. 在另一个终端运行测试
.venv\Scripts\python.exe test_api.py
```

