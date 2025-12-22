# Kinlin AI - API文档

## 基础信息

- **Base URL**: `http://localhost:8080/api`
- **API版本**: v1
- **认证方式**: 通过Header `X-User-Id`传递用户ID（开发阶段）

## 通用响应格式

### 成功响应
```json
{
  "success": true,
  "data": {...},
  "message": "操作成功"
}
```

### 错误响应
```json
{
  "success": false,
  "code": "ERROR_CODE",
  "message": "错误信息"
}
```

## API端点

### 1. 对话相关

#### 1.1 发送消息
- **URL**: `POST /chat`
- **Headers**: 
  - `X-User-Id`: 用户ID（可选）
  - `Content-Type`: application/json
- **Request Body**:
```json
{
  "text": "用户消息",
  "roleId": "角色ID（可选）",
  "contextId": "上下文ID（可选）",
  "fileUrl": "文件URL（可选）"
}
```
- **Response**:
```json
{
  "text": "AI回复",
  "contextId": "上下文ID",
  "confidence": 0.95
}
```

#### 1.2 清除对话历史
- **URL**: `DELETE /chat/{contextId}`
- **Response**: 204 No Content

#### 1.3 获取对话历史
- **URL**: `GET /chat/history/{contextId}`
- **Response**:
```json
[
  {
    "id": "消息ID",
    "role": "USER|ASSISTANT",
    "content": "消息内容",
    "createdAt": "2024-01-01T00:00:00"
  }
]
```

#### 1.4 评估对话质量
- **URL**: `GET /chat/quality/{contextId}`
- **Response**:
```json
{
  "score": 0.85,
  "feedback": "对话质量良好",
  "messageCount": 10
}
```

### 2. 角色相关

#### 2.1 获取内置角色列表
- **URL**: `GET /roles/builtin`
- **Response**:
```json
[
  {
    "id": "角色ID",
    "name": "律师",
    "description": "专业的法律顾问",
    "roleType": "BUILTIN"
  }
]
```

#### 2.2 获取自定义角色列表
- **URL**: `GET /roles/custom`
- **Headers**: `X-User-Id`: 用户ID
- **Response**: 同2.1

#### 2.3 获取角色详情
- **URL**: `GET /roles/{roleId}`
- **Response**: 单个角色对象

#### 2.4 创建自定义角色
- **URL**: `POST /roles/custom`
- **Headers**: `X-User-Id`: 用户ID
- **Request Body**:
```json
{
  "name": "角色名称",
  "description": "角色描述",
  "systemPrompt": "系统提示词",
  "dialogueStyle": {
    "formality": 0.8,
    "warmth": 0.6
  },
  "personality": {
    "严谨": true,
    "专业": true
  }
}
```

#### 2.5 更新角色
- **URL**: `PUT /roles/{roleId}`
- **Request Body**: 同2.4

#### 2.6 删除角色
- **URL**: `DELETE /roles/{roleId}`
- **Response**: 204 No Content

### 3. 语音相关

#### 3.1 发送语音消息
- **URL**: `POST /voice/chat`
- **Content-Type**: multipart/form-data
- **Parameters**:
  - `audio`: 音频文件
  - `roleId`: 角色ID（可选）
  - `contextId`: 上下文ID（可选）
- **Response**:
```json
{
  "text": "识别的文本",
  "contextId": "上下文ID",
  "confidence": 0.92
}
```

#### 3.2 文本转语音
- **URL**: `POST /voice/tts`
- **Content-Type**: multipart/form-data
- **Parameters**:
  - `text`: 要合成的文本
  - `voice`: 语音类型（可选，默认"default"）
- **Response**: 音频文件（application/octet-stream）

### 4. 文件相关

#### 4.1 上传文件
- **URL**: `POST /files/upload`
- **Content-Type**: multipart/form-data
- **Parameters**:
  - `file`: 文件
  - `type`: 文件类型（可选，默认"general"）
- **Response**:
```json
{
  "filePath": "文件路径",
  "originalFilename": "原始文件名",
  "size": 1024,
  "contentType": "image/png"
}
```

#### 4.2 下载文件
- **URL**: `GET /files/download/{type}/{filename}`
- **Response**: 文件流

#### 4.3 删除文件
- **URL**: `DELETE /files/{type}/{filename}`
- **Response**: 204 No Content

### 5. 搜索相关

#### 5.1 搜索对话消息
- **URL**: `GET /search/messages`
- **Parameters**:
  - `keyword`: 搜索关键词
  - `contextId`: 上下文ID（可选）
- **Response**: 消息列表

#### 5.2 搜索所有消息
- **URL**: `GET /search/all-messages`
- **Parameters**: `keyword`: 搜索关键词
- **Response**: 消息列表

### 6. 对话会话相关

#### 6.1 获取用户对话列表
- **URL**: `GET /conversations`
- **Headers**: `X-User-Id`: 用户ID
- **Response**: 对话列表

#### 6.2 获取对话详情
- **URL**: `GET /conversations/{contextId}`
- **Response**: 对话对象

#### 6.3 删除对话
- **URL**: `DELETE /conversations/{conversationId}`
- **Response**: 204 No Content

### 7. 用户相关

#### 7.1 获取当前用户信息
- **URL**: `GET /users/me`
- **Headers**: `X-User-Id`: 用户ID
- **Response**: 用户对象

#### 7.2 获取用户信息
- **URL**: `GET /users/{userId}`
- **Response**: 用户对象

### 8. 监控相关

#### 8.1 健康检查
- **URL**: `GET /health`
- **Response**:
```json
{
  "status": "UP",
  "service": "kinlin-ai-backend",
  "version": "1.0.0"
}
```

#### 8.2 获取系统指标
- **URL**: `GET /metrics`
- **Response**:
```json
{
  "apiRequests": 1000,
  "errors": 10,
  "messages": 500,
  "errorRate": 0.01
}
```

## WebSocket API

### 连接
- **URL**: `ws://localhost:8080/ws`
- **协议**: SockJS

### 发送消息
- **Destination**: `/app/chat/message`
- **Message**:
```json
{
  "text": "用户消息",
  "roleId": "角色ID",
  "contextId": "上下文ID"
}
```

### 接收消息
- **Destination**: `/topic/chat/{contextId}`
- **Message**: ChatResponse对象

## 错误码

| 错误码 | 说明 |
|--------|------|
| BUSINESS_ERROR | 业务错误 |
| RESOURCE_NOT_FOUND | 资源未找到 |
| VALIDATION_ERROR | 验证错误 |
| RATE_LIMIT_EXCEEDED | 请求过于频繁 |

## 限流说明

- 每个IP每分钟最多60个请求
- 响应头包含限流信息：
  - `X-RateLimit-Limit`: 限制数量
  - `X-RateLimit-Remaining`: 剩余数量

## Swagger文档

访问 `http://localhost:8080/swagger-ui.html` 查看完整的API文档。

---

**最后更新**：2024年

