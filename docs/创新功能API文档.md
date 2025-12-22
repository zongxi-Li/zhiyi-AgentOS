# Kinlin AI - 创新功能API文档

## 概述

本文档详细说明所有创新功能的API接口，包括数字人、情感感知、角色融合、知识图谱等功能。

**基础URL**: `http://localhost:8000/ai`

---

## 一、数字人API

### 1. 创建数字人

**接口**: `POST /digital-human/create`

**请求体**:
```json
{
  "role_id": "lawyer_001",
  "personality": "严谨、专业",
  "profession": "律师",
  "style": "realistic"  // realistic/cartoon/anime
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "avatar": {
      "model_type": "humanoid",
      "gender": "neutral",
      "age_range": "30-40",
      "appearance": {...},
      "render_style": "realistic"
    },
    "expressions": {
      "neutral": {...},
      "happy": {...},
      "sad": {...}
    },
    "animations": {
      "idle": {...},
      "speaking": {...}
    },
    "role_id": "lawyer_001"
  }
}
```

### 2. 更新数字人动画

**接口**: `POST /digital-human/animation`

**请求体**:
```json
{
  "role_id": "lawyer_001",
  "audio": "<base64编码的音频数据>",
  "text": "这是回复内容"
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "lip_sync": [...],
    "facial_expressions": [...],
    "body_gestures": [...],
    "duration": 2.5
  }
}
```

### 3. 切换数字人风格

**接口**: `POST /digital-human/style`

**请求体**:
```json
{
  "role_id": "lawyer_001",
  "new_style": "cartoon"  // realistic/cartoon/anime
}
```

---

## 二、情感感知API

### 1. 多模态情感分析

**接口**: `POST /emotion/analyze`

**请求体**:
```json
{
  "text": "我最近很焦虑，工作压力很大",
  "audio_features": {
    "pitch": 0.6,
    "energy": 0.7,
    "tempo": 0.5
  },
  "facial_features": {
    "expression": "worried",
    "intensity": 0.8
  }
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "emotion": "anxious",
    "intensity": 0.8,
    "confidence": 0.9,
    "all_scores": {
      "anxious": 0.8,
      "sad": 0.2,
      "neutral": 0.1
    }
  }
}
```

### 2. 生成情感感知回复

**接口**: `POST /emotion/response`

**请求体**:
```json
{
  "question": "我最近很焦虑",
  "base_role": {
    "role_id": "counselor",
    "personality": "温和、耐心",
    "knowledge_domain": ["心理", "情感"]
  },
  "text": "我最近很焦虑，工作压力很大",
  "audio_features": {...},
  "facial_features": {...}
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "text": "我理解你的担心，关于你的问题...",
    "animation": {
      "expression": "gentle_smile",
      "gesture": "nodding",
      "intensity": 0.7
    },
    "emotion": {
      "emotion": "understanding",
      "intensity": 0.7
    },
    "user_emotion": {
      "emotion": "anxious",
      "intensity": 0.8
    }
  }
}
```

---

## 三、角色融合API

### 1. 融合多个角色的回答

**接口**: `POST /role-fusion/fuse`

**请求体**:
```json
{
  "question": "我想创业，需要法律和商业建议",
  "available_roles": [
    {
      "role_id": "lawyer",
      "knowledge_domain": ["法律", "合同"],
      "personality": "严谨、专业"
    },
    {
      "role_id": "business",
      "knowledge_domain": ["商业", "策略"],
      "personality": "务实、创新"
    }
  ],
  "role_responses": {
    "lawyer": "从法律角度，需要注意合同条款...",
    "business": "从商业角度，建议考虑市场策略..."
  }
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "response": "综合多个专业角度的分析：\n\n1. 从法律角度...\n2. 从商业角度...",
    "style": {
      "formality": 0.7,
      "warmth": 0.6,
      "technical_level": 0.8
    },
    "weights": {
      "lawyer": 0.6,
      "business": 0.4
    },
    "sources": {
      "lawyer": "从法律角度...",
      "business": "从商业角度..."
    }
  }
}
```

### 2. 计算角色权重

**接口**: `POST /role-fusion/weights`

**请求体**:
```json
{
  "question": "我想创业，需要法律和商业建议",
  "available_roles": [
    {
      "role_id": "lawyer",
      "knowledge_domain": ["法律", "合同"]
    },
    {
      "role_id": "business",
      "knowledge_domain": ["商业", "策略"]
    }
  ]
}
```

---

## 四、知识图谱API

### 1. 构建知识图谱

**接口**: `POST /knowledge-graph/build`

**请求体**:
```json
{
  "documents": [
    {
      "doc_id": "doc1",
      "text": "张三是一名律师，属于ABC律师事务所。李四是该事务所的合伙人。",
      "metadata": {
        "source": "legal_doc",
        "date": "2024-01-01"
      }
    }
  ]
}
```

**响应**:
```json
{
  "success": true,
  "message": "知识图谱构建成功",
  "data": {
    "entities_count": 3,
    "triples_count": 2,
    "relations_count": 2
  }
}
```

### 2. 混合检索

**接口**: `POST /knowledge-graph/search`

**请求体**:
```json
{
  "question": "ABC律师事务所的律师有哪些？",
  "vector_db_results": [
    {
      "content": "...",
      "score": 0.8
    }
  ],
  "top_k": 5
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "kg_results": [
      {
        "entity": "person_张三",
        "relation": "属于",
        "weight": 0.8
      }
    ],
    "vector_results": [...],
    "fused_results": [...],
    "entities": [
      {
        "id": "person_张三",
        "text": "张三",
        "type": "person"
      }
    ]
  }
}
```

### 3. 知识推理

**接口**: `POST /knowledge-graph/reason`

**请求体**:
```json
{
  "question": "张三和李四的关系是什么？"
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "reasoning_paths": [
      [
        ["属于", "org_ABC律师事务所"],
        ["合伙人", "person_李四"]
      ]
    ],
    "conclusions": [
      "通过路径: 属于(org_ABC律师事务所) -> 合伙人(person_李四)"
    ],
    "entities": [...],
    "relations": ["关系"]
  }
}
```

### 4. 获取图谱统计

**接口**: `GET /knowledge-graph/stats`

**响应**:
```json
{
  "success": true,
  "data": {
    "entities_count": 10,
    "triples_count": 15,
    "relations_count": 8,
    "entities": ["entity1", "entity2", ...]
  }
}
```

### 5. 查询实体信息

**接口**: `GET /knowledge-graph/entity/{entity_id}?relation=属于&limit=10`

**响应**:
```json
{
  "success": true,
  "data": {
    "entity": {
      "id": "person_张三",
      "type": "person",
      "properties": {}
    },
    "related_entities": [
      {
        "entity": "org_ABC律师事务所",
        "relation": "属于",
        "weight": 0.8
      }
    ]
  }
}
```

---

## 五、增强的对话API

### 文本对话（支持情感感知）

**接口**: `POST /chat/text`

**请求体**:
```json
{
  "text": "我最近很焦虑",
  "role_id": "counselor",
  "context": [],
  "enable_emotion_aware": true,
  "audio_features": {
    "pitch": 0.6,
    "energy": 0.7
  }
}
```

**响应**:
```json
{
  "text": "我理解你的担心，关于你的问题...",
  "confidence": 0.85,
  "emotion": {
    "emotion": "understanding",
    "intensity": 0.7
  },
  "user_emotion": {
    "emotion": "anxious",
    "intensity": 0.8
  },
  "animation": {...},
  "emotion_aware": true
}
```

---

## 六、增强的RAG API

### RAG查询（支持知识图谱）

**接口**: `POST /rag/query`

**请求体**:
```json
{
  "query": "ABC律师事务所的律师有哪些？",
  "top_k": 5,
  "use_knowledge_graph": true
}
```

**响应**:
```json
{
  "answer": "根据知识库和知识图谱，ABC律师事务所的律师包括...",
  "sources": [...],
  "confidence": 0.9,
  "kg_info": {
    "use_kg": true,
    "entities": [...],
    "kg_results": [...]
  }
}
```

---

## 七、错误处理

所有API在出错时返回统一格式：

```json
{
  "detail": "错误信息"
}
```

**HTTP状态码**:
- `200`: 成功
- `400`: 请求参数错误
- `404`: 资源不存在
- `500`: 服务器内部错误

---

## 八、使用示例

### Python示例

```python
import requests

# 创建数字人
response = requests.post(
    "http://localhost:8000/ai/digital-human/create",
    json={
        "role_id": "lawyer_001",
        "personality": "严谨、专业",
        "profession": "律师",
        "style": "realistic"
    }
)
print(response.json())

# 情感分析
response = requests.post(
    "http://localhost:8000/ai/emotion/analyze",
    json={
        "text": "我最近很焦虑",
        "audio_features": {"pitch": 0.6, "energy": 0.7}
    }
)
print(response.json())
```

### JavaScript示例

```javascript
// 创建数字人
fetch('http://localhost:8000/ai/digital-human/create', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    role_id: 'lawyer_001',
    personality: '严谨、专业',
    profession: '律师',
    style: 'realistic'
  })
})
.then(res => res.json())
.then(data => console.log(data));
```

---

**最后更新**: 2024年

