# Kinlin AI - 系统多功能交互助手

## 项目概述

本项目是基于银河麒麟操作系统和麒麟AI SDK开发的系统多功能交互助手，旨在为用户提供智能化的文本和语音交互体验。系统支持多种内置角色和自定义角色功能，能够满足不同场景下的对话需求。

### 🌟 核心创新功能

- **智能数字人角色系统**: AIGC生成数字人形象，实时语音驱动，多风格切换
- **情感感知对话**: 多模态情感识别，情感驱动的个性化回复
- **智能角色融合**: 多角色协同，融合不同专业角度的回答
- **知识图谱增强RAG**: 结构化知识检索，支持知识推理
- **联邦学习优化**: 隐私保护的模型持续优化

**详细说明**: 请参考 [创新点完整实现说明](./docs/创新点完整实现说明.md) 和 [创新功能API文档](./docs/创新功能API文档.md)

## 项目目标

开发一个功能完整、交互流畅的AI助手系统，具备以下核心能力：
- 高效的文本对话处理
- 实时语音识别与合成
- 多角色智能对话
- 灵活的角色自定义功能

## 功能需求

### 1. 文本对话功能

#### 功能描述
实现高效准确的自然语言理解，能够理解用户提出的各类问题，并给出合理、有针对性的回答。

#### 核心特性
- **自然语言理解**：能够准确理解用户提出的各类问题
- **智能回答**：提供合理、有针对性的回答
- **多轮对话**：支持多轮对话，保持对话的连贯性和逻辑性
- **上下文理解**：根据上下文准确理解用户意图

#### 使用方法
```python
# 示例：文本对话接口
from kinlin_ai import TextChat

chat = TextChat()
response = chat.send_message("你好，我想了解一下法律问题")
print(response)
```

#### 参数说明
- `message` (str): 用户输入的文本消息
- `context` (list, optional): 对话历史上下文，默认为空列表
- `role` (str, optional): 使用的角色类型，默认为通用助手

#### 返回值说明
- 返回 `dict` 类型，包含以下字段：
  - `response` (str): AI助手的回复文本
  - `confidence` (float): 回答的置信度（0-1）
  - `context_id` (str): 对话上下文ID

### 2. 语音对话功能

#### 功能描述
集成高质量的语音识别和语音合成功能，实现实时语音交互。

#### 核心特性
- **语音识别（ASR）**：实时准确地将用户语音转换为文本
- **语音合成（TTS）**：自然流畅的语音合成能力
- **实时处理**：支持实时语音输入和输出

#### 使用方法
```python
# 示例：语音对话接口
from kinlin_ai import VoiceChat

voice_chat = VoiceChat()
# 语音输入
text = voice_chat.speech_to_text(audio_file="input.wav")
# 语音输出
voice_chat.text_to_speech(text="这是回复内容", output_file="output.wav")
```

#### 参数说明
- `audio_file` (str): 输入的音频文件路径
- `text` (str): 需要转换为语音的文本
- `output_file` (str): 输出的音频文件路径
- `language` (str, optional): 语言类型，默认为"zh-CN"

#### 返回值说明
- `speech_to_text()`: 返回识别出的文本字符串
- `text_to_speech()`: 返回生成的音频文件路径

### 3. 内置角色功能

#### 功能描述
系统内置至少4种专业角色，每个角色都有独特的对话风格和专业知识。

#### 内置角色列表

##### 3.1 律师角色
- **专业领域**：法律咨询、法律建议
- **对话风格**：严谨、专业、逻辑清晰
- **功能**：解答常见的法律问题，提供法律建议

##### 3.2 教师角色
- **专业领域**：知识讲解、学习辅导
- **对话风格**：耐心、细致、循循善诱
- **功能**：进行知识讲解、辅导学习

##### 3.3 程序员角色
- **专业领域**：代码问题排查、编程建议
- **对话风格**：简洁、技术导向、注重实践
- **功能**：协助代码问题排查、提供编程建议

##### 3.4 作家角色
- **专业领域**：创意写作、文章润色
- **对话风格**：富有创意、文采斐然
- **功能**：进行创意写作、文章润色等

#### 使用方法
```python
# 示例：使用内置角色
from kinlin_ai import RoleChat

# 使用律师角色
lawyer = RoleChat(role="lawyer")
response = lawyer.chat("合同纠纷如何处理？")

# 使用教师角色
teacher = RoleChat(role="teacher")
response = teacher.chat("请解释一下什么是机器学习")

# 使用程序员角色
programmer = RoleChat(role="programmer")
response = programmer.chat("如何优化Python代码性能？")

# 使用作家角色
writer = RoleChat(role="writer")
response = writer.chat("帮我写一段关于春天的散文")
```

#### 参数说明
- `role` (str): 角色类型，可选值：`"lawyer"`, `"teacher"`, `"programmer"`, `"writer"`
- `message` (str): 用户输入的消息

#### 返回值说明
- 返回 `dict` 类型，包含角色回复和相关元数据

### 4. 自定义角色功能

#### 功能描述
用户可以通过直观易用的界面创建自定义角色，设定角色的描述、对话风格等信息。

#### 核心特性
- **角色创建**：通过输入角色描述、对话风格示例等信息创建自定义角色
- **风格定制**：根据用户设定的规则进行对话，展现出独特的风格和特点
- **角色管理**：支持角色的保存、加载、删除等管理功能

#### 使用方法
```python
# 示例：创建自定义角色
from kinlin_ai import CustomRole

# 创建自定义角色
custom_role = CustomRole.create(
    name="心理咨询师",
    description="专业的心理咨询师，擅长倾听和引导",
    style_examples=[
        "用户：我最近很焦虑\n角色：我理解你的感受，能详细说说是什么让你感到焦虑吗？",
        "用户：工作压力大\n角色：工作压力确实会影响我们的情绪，你平时是如何缓解压力的呢？"
    ],
    personality="温和、耐心、专业、富有同理心"
)

# 使用自定义角色
response = custom_role.chat("我最近总是失眠")
```

#### 参数说明
- `name` (str): 角色名称
- `description` (str): 角色描述
- `style_examples` (list): 对话风格示例列表
- `personality` (str): 角色性格特点

#### 返回值说明
- `create()`: 返回创建的自定义角色对象
- `chat()`: 返回角色的回复文本

## 技术架构

### 核心技术栈
- **操作系统**：银河麒麟操作系统
- **AI SDK**：麒麟AI SDK
- **编程语言**：Python 3.x
- **文档处理**：easydoc, mineru
- **RAG技术**：ragflow, qanything, fastgpt

### 系统架构设计

```
┌─────────────────────────────────────────┐
│         用户交互层 (UI Layer)            │
│  ┌──────────┐  ┌──────────┐            │
│  │ 文本输入  │  │ 语音输入  │            │
│  └──────────┘  └──────────┘            │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│       对话处理层 (Chat Layer)            │
│  ┌──────────┐  ┌──────────┐            │
│  │ 文本对话  │  │ 语音对话  │            │
│  └──────────┘  └──────────┘            │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│       角色管理层 (Role Layer)            │
│  ┌──────────┐  ┌──────────┐            │
│  │ 内置角色  │  │ 自定义角色 │            │
│  └──────────┘  └──────────┘            │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│      AI引擎层 (AI Engine Layer)          │
│  ┌──────────┐  ┌──────────┐            │
│  │ 麒麟AI SDK│  │ RAG引擎   │            │
│  └──────────┘  └──────────┘            │
└─────────────────────────────────────────┘
```

### 模块设计

#### 1. 文本对话模块 (TextChat)
- 负责处理文本输入和输出
- 实现多轮对话上下文管理
- 集成自然语言理解功能

#### 2. 语音对话模块 (VoiceChat)
- 负责语音识别（ASR）
- 负责语音合成（TTS）
- 处理音频文件的输入输出

#### 3. 角色管理模块 (RoleManager)
- 管理内置角色配置
- 处理自定义角色的创建和管理
- 实现角色切换和角色特性应用

#### 4. AI引擎模块 (AIEngine)
- 封装麒麟AI SDK接口
- 实现RAG检索增强生成
- 处理模型推理和响应生成

### 麒麟AI SDK集成说明

#### SDK初始化
```python
from kylin_ai_sdk import KylinAIClient

# 初始化客户端
client = KylinAIClient(
    api_key="your_api_key",
    api_endpoint="https://api.kylin.ai",
    timeout=30
)
```

#### 文本生成
```python
# 使用麒麟AI SDK进行文本生成
response = await client.text_generation.generate(
    prompt="用户输入的问题",
    max_tokens=512,
    temperature=0.7,
    context=conversation_history
)
```

#### 语音识别
```python
# 使用麒麟AI SDK进行语音识别
result = await client.speech_recognition.recognize(
    audio_data=audio_bytes,
    language="zh-CN"
)
```

#### 语音合成
```python
# 使用麒麟AI SDK进行语音合成
audio = await client.speech_synthesis.synthesize(
    text="要合成的文本",
    voice="default",
    speed=1.0
)
```

详细集成说明请参考 [后端设计文档](./docs/后端设计文档.md#2-麒麟ai-sdk集成)

## 开发环境

### 系统要求
- 操作系统：银河麒麟操作系统
- Python版本：Python 3.8+
- 内存：建议8GB以上
- 存储：建议20GB以上可用空间

### 依赖安装
```bash
# 安装Python依赖
pip install -r requirements.txt

# 安装麒麟AI SDK
# 根据麒麟AI SDK官方文档进行安装
```

## 项目结构

```
Kinlin_AI/
├── README.md                 # 项目说明文档（本文件）
├── TODO.md                   # 开发任务清单
├── requirements.txt          # Python依赖包列表
├── config/                   # 配置文件目录
│   ├── config.yaml          # 主配置文件
│   └── roles.yaml           # 角色配置文件
├── src/                      # 源代码目录
│   ├── __init__.py
│   ├── text_chat.py         # 文本对话模块
│   ├── voice_chat.py        # 语音对话模块
│   ├── role_manager.py      # 角色管理模块
│   ├── ai_engine.py         # AI引擎模块
│   └── utils/               # 工具函数
│       ├── __init__.py
│       └── logger.py        # 日志工具
├── tests/                    # 测试文件目录
│   ├── test_text_chat.py
│   ├── test_voice_chat.py
│   └── test_roles.py
├── docs/                     # 文档目录
│   └── api.md               # API文档
└── data/                     # 数据目录
    └── roles/               # 角色数据存储
```

## 配置说明

### 配置文件结构

#### config.yaml 主配置文件
```yaml
# 麒麟AI SDK配置
ai_sdk:
  api_key: "your_api_key_here"
  api_endpoint: "https://api.example.com"
  timeout: 30
  max_retries: 3
  model: "default"

# 文本对话配置
text_chat:
  max_context_length: 4096
  temperature: 0.7
  top_p: 0.9
  enable_cache: true
  cache_ttl: 3600

# 语音对话配置
voice_chat:
  asr:
    language: "zh-CN"
    sample_rate: 16000
    format: "wav"
    enable_punctuation: true
  tts:
    voice: "default"
    speed: 1.0
    pitch: 1.0
    volume: 1.0

# RAG配置
rag:
  enabled: true
  provider: "ragflow"  # ragflow, qanything, fastgpt
  knowledge_base_path: "./data/knowledge_base"
  top_k: 5
  similarity_threshold: 0.7

# 日志配置
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  file: "./logs/kinlin_ai.log"
  max_size: 10485760  # 10MB
  backup_count: 5

# 性能配置
performance:
  max_concurrent_requests: 10
  request_timeout: 60
  enable_rate_limiting: true
  rate_limit_per_minute: 60
```

#### roles.yaml 角色配置文件
```yaml
builtin_roles:
  lawyer:
    name: "律师"
    description: "专业的法律顾问，擅长解答法律问题"
    personality: "严谨、专业、逻辑清晰"
    knowledge_domain: ["法律", "合同", "纠纷"]
    system_prompt: "你是一位经验丰富的律师..."
    
  teacher:
    name: "教师"
    description: "耐心的教育工作者，擅长知识讲解"
    personality: "耐心、细致、循循善诱"
    knowledge_domain: ["教育", "学习", "知识"]
    system_prompt: "你是一位优秀的教师..."
    
  programmer:
    name: "程序员"
    description: "技术专家，擅长解决编程问题"
    personality: "简洁、技术导向、注重实践"
    knowledge_domain: ["编程", "代码", "技术"]
    system_prompt: "你是一位资深的程序员..."
    
  writer:
    name: "作家"
    description: "创意写作者，擅长文字创作"
    personality: "富有创意、文采斐然"
    knowledge_domain: ["写作", "文学", "创意"]
    system_prompt: "你是一位才华横溢的作家..."
```

## API文档

### 核心API接口

#### TextChat 类

```python
class TextChat:
    def __init__(self, config_path: str = None):
        """初始化文本对话系统
        
        Args:
            config_path: 配置文件路径，默认为None使用默认配置
        """
        
    def send_message(
        self, 
        message: str, 
        context: List[Dict] = None,
        role: str = None,
        temperature: float = None
    ) -> Dict:
        """发送文本消息
        
        Args:
            message: 用户输入的文本消息
            context: 对话历史上下文，格式为 [{"role": "user", "content": "..."}, ...]
            role: 使用的角色类型，可选值：lawyer, teacher, programmer, writer
            temperature: 生成温度，控制回复的随机性（0-1）
            
        Returns:
            Dict包含以下字段：
            - response (str): AI助手的回复文本
            - confidence (float): 回答的置信度（0-1）
            - context_id (str): 对话上下文ID
            - tokens_used (int): 使用的token数量
            - response_time (float): 响应时间（秒）
            
        Raises:
            ValueError: 当参数无效时
            APIError: 当API调用失败时
        """
        
    def get_history(self, context_id: str) -> List[Dict]:
        """获取对话历史
        
        Args:
            context_id: 对话上下文ID
            
        Returns:
            对话历史列表
        """
        
    def clear_history(self, context_id: str) -> bool:
        """清除对话历史
        
        Args:
            context_id: 对话上下文ID
            
        Returns:
            是否清除成功
        """
```

#### VoiceChat 类

```python
class VoiceChat:
    def __init__(self, config_path: str = None):
        """初始化语音对话系统"""
        
    def speech_to_text(
        self,
        audio_file: str = None,
        audio_data: bytes = None,
        language: str = "zh-CN"
    ) -> Dict:
        """语音转文本
        
        Args:
            audio_file: 音频文件路径
            audio_data: 音频数据（字节流）
            language: 语言类型，默认"zh-CN"
            
        Returns:
            Dict包含以下字段：
            - text (str): 识别出的文本
            - confidence (float): 识别置信度
            - duration (float): 音频时长（秒）
            
        Raises:
            ValueError: 当参数无效时
            FileNotFoundError: 当音频文件不存在时
        """
        
    def text_to_speech(
        self,
        text: str,
        output_file: str = None,
        voice: str = "default",
        speed: float = 1.0,
        pitch: float = 1.0
    ) -> Dict:
        """文本转语音
        
        Args:
            text: 需要转换的文本
            output_file: 输出音频文件路径
            voice: 语音类型
            speed: 语速（0.5-2.0）
            pitch: 音调（0.5-2.0）
            
        Returns:
            Dict包含以下字段：
            - audio_file (str): 生成的音频文件路径
            - duration (float): 音频时长（秒）
        """
        
    def realtime_chat(self, callback=None):
        """实时语音对话
        
        Args:
            callback: 回调函数，接收识别结果和合成音频
        """
```

#### RoleManager 类

```python
class RoleManager:
    def __init__(self, config_path: str = None):
        """初始化角色管理器"""
        
    def get_builtin_roles(self) -> List[Dict]:
        """获取所有内置角色列表"""
        
    def get_role(self, role_name: str) -> Dict:
        """获取指定角色的配置"""
        
    def create_custom_role(
        self,
        name: str,
        description: str,
        style_examples: List[str],
        personality: str
    ) -> CustomRole:
        """创建自定义角色"""
        
    def save_custom_role(self, role: CustomRole) -> bool:
        """保存自定义角色"""
        
    def load_custom_role(self, role_id: str) -> CustomRole:
        """加载自定义角色"""
        
    def delete_custom_role(self, role_id: str) -> bool:
        """删除自定义角色"""
```

## 使用指南

### 快速开始

1. **环境准备**
   ```bash
   # 克隆项目
   git clone <repository_url>
   cd Kinlin_AI
   
   # 创建虚拟环境（推荐）
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或
   venv\Scripts\activate  # Windows
   
   # 安装依赖
   pip install -r requirements.txt
   ```

2. **配置设置**
   ```bash
   # 复制配置模板
   cp config/config.yaml.example config/config.yaml
   
   # 编辑配置文件
   vim config/config.yaml
   # 设置麒麟AI SDK的API密钥等信息
   ```

3. **运行示例**
   ```bash
   # 运行文本对话示例
   python examples/text_chat_example.py
   
   # 运行语音对话示例
   python examples/voice_chat_example.py
   
   # 运行角色管理示例
   python examples/role_example.py
   ```

### 基本使用流程

#### 文本对话示例
```python
from kinlin_ai import TextChat

# 初始化对话系统
chat = TextChat()

# 简单对话
response = chat.send_message("你好")
print(response['response'])

# 使用特定角色
response = chat.send_message(
    "合同纠纷如何处理？",
    role="lawyer"
)
print(response['response'])

# 多轮对话
context_id = None
for i in range(3):
    message = input("你: ")
    result = chat.send_message(message, context_id=context_id)
    print(f"AI: {result['response']}")
    context_id = result['context_id']
```

#### 语音对话示例
```python
from kinlin_ai import VoiceChat

# 初始化语音系统
voice = VoiceChat()

# 语音转文本
result = voice.speech_to_text("input.wav")
print(f"识别结果: {result['text']}")

# 文本转语音
result = voice.text_to_speech(
    "这是回复内容",
    output_file="output.wav"
)
print(f"音频已保存到: {result['audio_file']}")
```

#### 自定义角色示例
```python
from kinlin_ai import RoleManager, TextChat

# 创建角色管理器
role_manager = RoleManager()

# 创建自定义角色
custom_role = role_manager.create_custom_role(
    name="心理咨询师",
    description="专业的心理咨询师",
    style_examples=[
        "用户：我最近很焦虑\n角色：我理解你的感受...",
    ],
    personality="温和、耐心、专业"
)

# 保存角色
role_manager.save_custom_role(custom_role)

# 使用自定义角色
chat = TextChat()
response = chat.send_message(
    "我最近总是失眠",
    role=custom_role.id
)
```

## 错误处理与异常

### 错误类型

系统定义了以下异常类型：

```python
class KinlinAIError(Exception):
    """基础异常类"""
    pass

class APIError(KinlinAIError):
    """API调用错误"""
    pass

class ConfigurationError(KinlinAIError):
    """配置错误"""
    pass

class RoleError(KinlinAIError):
    """角色相关错误"""
    pass

class AudioError(KinlinAIError):
    """音频处理错误"""
    pass
```

### 错误处理机制

1. **自动重试**：网络请求失败时自动重试（最多3次）
2. **降级策略**：当主要服务不可用时，使用备用方案
3. **错误日志**：所有错误都会记录到日志文件
4. **用户提示**：提供友好的错误提示信息

### 错误处理示例

```python
from kinlin_ai import TextChat, APIError

try:
    chat = TextChat()
    response = chat.send_message("你好")
except APIError as e:
    print(f"API调用失败: {e}")
    # 可以尝试使用备用配置
except Exception as e:
    print(f"发生未知错误: {e}")
```

## 性能优化

### 优化策略

1. **对话缓存**
   - 缓存常见问题的回答
   - 减少重复的API调用
   - 缓存TTL可配置

2. **并发处理**
   - 支持多请求并发处理
   - 使用异步IO提升性能
   - 连接池管理

3. **上下文压缩**
   - 智能压缩长对话历史
   - 保留关键上下文信息
   - 减少token消耗

4. **批量处理**
   - 支持批量文本处理
   - 批量语音转换
   - 提升处理效率

### 性能指标

- **文本对话响应时间**：< 2秒（平均）
- **语音识别延迟**：< 1秒（实时模式）
- **语音合成速度**：实时倍速 1.0x
- **并发处理能力**：支持10+并发请求

## 安全考虑

### 数据安全

1. **API密钥管理**
   - 使用环境变量存储敏感信息
   - 配置文件不提交到版本控制
   - 支持密钥轮换

2. **数据加密**
   - 对话历史加密存储
   - 传输数据使用HTTPS
   - 敏感信息脱敏处理

3. **访问控制**
   - 实现请求频率限制
   - IP白名单支持
   - 用户认证机制

### 隐私保护

1. **数据最小化**：只收集必要的对话数据
2. **数据保留**：可配置的数据保留期限
3. **用户控制**：用户可以删除自己的对话历史

## 监控与调试

### 日志系统

系统内置完善的日志记录功能，支持多级别日志：

```python
# 日志级别
DEBUG    # 详细的调试信息
INFO     # 一般信息
WARNING  # 警告信息
ERROR    # 错误信息
CRITICAL # 严重错误
```

日志配置示例：
```yaml
logging:
  level: "INFO"
  file: "./logs/kinlin_ai.log"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  max_size: 10485760  # 10MB
  backup_count: 5
```

### 性能监控

使用系统监控工具监控系统资源：

```bash
# CPU和内存监控
top
htop

# 系统统计信息
vmstat 1

# I/O统计
iostat -x 1

# 系统消息
dmesg | tail

# 网络监控
nmon
```

### 调试工具

1. **日志分析**：分析日志文件定位问题
2. **性能分析**：使用cProfile分析性能瓶颈
3. **API测试**：使用Postman或curl测试API接口

### 错误处理
- 所有模块都包含完善的错误处理机制
- 错误信息会记录到日志文件
- 提供友好的错误提示给用户
- 支持错误上报和追踪

## 开发计划

详细的开发任务和进度请参考 [TODO.md](./TODO.md) 文件。

## 许可证

MIT License

## 设计文档

### 📘 完整项目方案（推荐）
**所有方案内容已整合到一个文档中，分段组织，便于阅读：**
- [完整项目方案文档](./docs/完整项目方案.md) ⭐

该文档包含：
- 第一部分：项目概述与需求分析
- 第二部分：技术架构设计
- 第三部分：前端设计
- 第四部分：后端设计
- 第五部分：创新点设计
- 第六部分：实施计划
- 第七部分：总结

### 分模块详细文档

如需查看各模块的详细设计，可参考以下文档：

#### 前端设计文档
详细的前端架构、组件设计、状态管理、API接口等，请参考：
- [前端设计文档](./docs/前端设计文档.md)

#### 后端设计文档
详细的后端架构、API设计、数据库设计、麒麟AI SDK集成等，请参考：
- [后端设计文档](./docs/后端设计文档.md)

#### 创新点说明
详细的创新点技术方案、实现细节等，请参考：
- [创新点说明文档](./docs/创新点说明.md)

#### 创新点分析与建议 ⭐ 新增
深入分析当前系统创新点，并提出技术创新方向建议，请参考：
- [创新点分析与建议文档](./docs/创新点分析与建议.md)

该文档包含：
- 当前系统创新点分类分析
- 操作系统层面技术创新建议（AI加速框架、资源调度、安全沙箱）
- 系统架构层面创新建议（分布式推理、模型热更新）
- 算法层面创新建议（自适应上下文压缩）
- 应用创新 vs 技术创新对比分析
- 技术创新优先级和实施建议

#### 创新点完整实现说明 ⭐ 新增
所有创新点的完整实现代码和使用说明，请参考：
- [创新点完整实现说明文档](./docs/创新点完整实现说明.md)

#### 实现状态检查报告 ⭐ 新增
详细的实现状态和集成进度，请参考：
- [实现状态检查报告](./docs/实现状态检查报告.md)

#### 创新功能API文档 ⭐ 新增
所有创新功能的API接口详细说明，请参考：
- [创新功能API文档](./docs/创新功能API文档.md)

#### 创新功能快速开始 ⭐ 新增
快速上手使用创新功能的指南，请参考：
- [创新功能快速开始](./docs/创新功能快速开始.md)

#### 完成总结 ⭐ 新增
实现完成情况总结，请参考：
- [完成总结](./docs/完成总结.md)

#### 数据使用说明 ⭐ 新增
数据存储方式和必填字段说明，请参考：
- [数据使用说明](./docs/数据使用说明.md)

#### PostgreSQL数据库使用指南 ⭐ 新增
详细的PostgreSQL数据库使用说明，请参考：
- [PostgreSQL数据库使用指南](./docs/PostgreSQL数据库使用指南.md)

该文档包含：
- 数据库安装和配置（Docker/本地安装）
- 数据库表结构详细说明
- 如何使用数据库（JPA Repository）
- 常用操作示例（CRUD、查询、统计）
- 数据库迁移（Flyway）
- 连接测试和常见问题

该文档包含：
- 数据存储方式（数据库、Redis、文件、内存）
- 各存储方式的必要性说明
- 所有API的必填字段和可选字段
- 功能依赖关系图
- 部署建议

该文档包含：
- 数字人API（创建、动画、风格切换）
- 情感感知API（情感分析、情感感知回复）
- 角色融合API（多角色融合、权重计算）
- 知识图谱API（构建、检索、推理）
- 增强的对话和RAG API
- 完整的请求/响应示例

**当前实现状态**：
- ✅ **核心服务代码**: 100% 完成（5个服务文件已创建）
- ⚠️ **系统集成**: 40% 完成（API接口已创建，待完善）
- ⚠️ **功能优化**: 50% 完成（部分功能为简化实现，需集成专业模型）

**总体完成度**: 70%

## 参考资料

- **麒麟AI SDK开发手册** - 核心AI能力SDK
- **easydoc** - 文档处理工具
- **mineru** - 文档处理工具
- **ragflow** - RAG框架
- **qanything** - RAG框架
- **fastgpt** - RAG框架

## 部署指南

### 本地部署

1. **环境准备**
   ```bash
   # 确保Python 3.8+已安装
   python --version
   
   # 安装系统依赖（银河麒麟系统）
   sudo apt-get update
   sudo apt-get install -y python3-pip python3-venv
   ```

2. **项目部署**
   ```bash
   # 克隆项目
   git clone <repository_url>
   cd Kinlin_AI
   
   # 创建虚拟环境
   python3 -m venv venv
   source venv/bin/activate
   
   # 安装依赖
   pip install -r requirements.txt
   
   # 配置环境
   cp config/config.yaml.example config/config.yaml
   # 编辑配置文件，填入API密钥等信息
   ```

3. **启动服务**
   ```bash
   # 启动Web服务（如果实现）
   python app.py
   
   # 或使用命令行接口
   python cli.py
   ```

### Docker部署

```dockerfile
# Dockerfile示例
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "app.py"]
```

```bash
# 构建镜像
docker build -t kinlin-ai .

# 运行容器
docker run -d -p 8000:8000 \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  kinlin-ai
```

### 生产环境部署

1. **使用进程管理器**
   ```bash
   # 使用systemd
   sudo systemctl start kinlin-ai
   sudo systemctl enable kinlin-ai
   ```

2. **反向代理配置**（Nginx示例）
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

3. **监控和日志**
   - 配置日志轮转
   - 设置监控告警
   - 定期备份数据

## 创新点

### 1. 智能数字人角色系统
**创新描述**：基于AIGC技术，为每个角色创建专属的数字人形象，支持实时语音驱动、表情动作生成，提供可视化的沉浸式交互体验。结合银河麒麟操作系统的图形界面优势，实现流畅的数字人渲染和交互。

**技术实现**：
- 数字人形象生成（AIGC）
- 实时语音驱动（Lip Sync）
- 银河麒麟系统优化渲染
- 多风格数字人切换

**应用场景**：
- 可视化角色对话
- 沉浸式交互体验
- 桌面助手集成

### 2. 银河麒麟系统深度集成
**创新描述**：深度集成银河麒麟操作系统，充分利用系统服务、安全机制、桌面环境等特性，提供原生化、高性能、安全可靠的AI助手体验。

**技术实现**：
- 系统服务集成
- 安全机制集成
- 系统资源监控
- 系统级快捷操作

**应用场景**：
- 系统级助手
- 安全可靠服务
- 性能优化体验

### 3. 情感感知数字人对话
**创新描述**：结合情感感知技术和数字人AIGC，数字人能够根据用户的情感状态实时调整表情、动作、语音语调，提供更有同理心、更真实的交互体验。

**技术实现**：
- 多模态情感识别
- 数字人情感表达
- 情感驱动的对话生成

**应用场景**：
- 情感化交互
- 心理咨询场景
- 教育辅导场景

### 4. 联邦学习模型优化
**创新描述**：采用联邦学习技术，在保护用户隐私的前提下，利用多用户数据持续优化AI模型。结合银河麒麟操作系统的安全机制，实现安全、高效的分布式模型训练。

**技术实现**：
- 联邦学习框架
- 差分隐私保护
- 联邦学习与数字人结合
- 银河麒麟系统安全集成

**应用场景**：
- 隐私保护训练
- 持续模型优化
- 跨设备学习

**优势**：
- 数据不出本地，保护隐私
- 多用户协同优化
- 符合数据安全法规

### 5. 智能模型选择系统
**创新描述**：构建多模型管理框架，根据任务类型、用户偏好、系统资源等因素，智能选择最优模型进行推理。结合联邦学习优化结果，动态调整模型选择策略。

**技术实现**：
- 多模型管理框架
- 模型选择策略（性能/速度/平衡/自适应）
- 联邦学习优化模型选择
- 数字人模型选择
- 实时模型切换

**应用场景**：
- 性能优化
- 资源适配
- 用户体验优化
- 成本控制

**优势**：
- 为每个任务选择最合适的模型
- 根据系统资源智能选择
- 平衡性能和成本

### 6. 智能角色融合技术
**创新描述**：实现多角色协同对话，允许用户同时启用多个角色，系统智能融合不同角色的专业知识和对话风格，提供更全面、多角度的回答。

**技术实现**：
- 角色权重分配算法
- 多角色知识融合机制
- 智能风格平衡系统

**应用场景**：
- 复杂问题需要多领域专业知识
- 需要从不同角度分析问题
- 跨领域咨询场景

**示例**：
```
用户：我想创业，需要法律和商业建议
系统：融合律师角色（法律风险）+ 商业顾问角色（商业策略）
```

### 2. 情感感知对话系统
**创新描述**：通过分析用户文本和语音的情感特征，系统能够感知用户情绪状态，并相应调整对话风格和回复内容，提供更有同理心的交互体验。

**技术实现**：
- 情感分析模型集成
- 语音情感识别
- 情感驱动的回复生成

**应用场景**：
- 心理咨询场景
- 客户服务场景
- 教育辅导场景

**示例**：
```
检测到用户情绪：焦虑
系统自动切换到更温和、耐心的对话风格
```

### 3. 知识图谱增强RAG
**创新描述**：结合知识图谱技术，构建结构化的知识体系，在RAG检索时不仅返回相关文档，还能提供知识图谱中的关联信息，增强回答的准确性和关联性。

**技术实现**：
- 知识图谱构建
- 图谱与文档联合检索
- 知识推理机制

**应用场景**：
- 专业领域问答（法律、医疗等）
- 复杂问题推理
- 知识关联查询

**优势**：
- 回答更准确
- 信息关联性更强
- 支持推理查询

### 4. 自适应学习角色系统
**创新描述**：自定义角色不仅基于用户提供的示例，还能在对话过程中持续学习用户的偏好和反馈，自动优化角色的对话风格和知识范围。

**技术实现**：
- 在线学习算法
- 用户反馈收集
- 角色参数自适应调整

**应用场景**：
- 长期使用的个人助手
- 企业定制化助手
- 专业领域助手

**特点**：
- 越用越智能
- 个性化程度高
- 持续优化

### 5. 多模态交互增强
**创新描述**：不仅支持文本和语音，还支持图片、文档等多种输入形式，系统能够理解多模态内容，提供更丰富的交互体验。

**技术实现**：
- 图像理解（OCR、图像描述）
- 文档解析（PDF、Word等）
- 多模态融合理解

**应用场景**：
- 文档问答
- 图片内容理解
- 混合内容分析

**示例**：
```
用户上传合同图片 → 系统OCR识别 → 律师角色分析 → 提供法律建议
```

### 6. 对话记忆与个性化
**创新描述**：系统建立长期对话记忆，能够记住用户的历史偏好、重要信息、对话习惯等，提供个性化的、有记忆的对话体验。

**技术实现**：
- 长期记忆存储
- 用户画像构建
- 个性化推荐

**应用场景**：
- 个人助手
- 客户服务
- 学习伙伴

**特点**：
- 记住用户偏好
- 上下文连贯性更强
- 个性化程度高

### 7. 实时协作对话
**创新描述**：支持多用户同时与同一角色对话，系统能够协调多用户的问题，提供协作式的对话体验，适合团队使用场景。

**技术实现**：
- 多用户会话管理
- 问题协调机制
- 协作上下文维护

**应用场景**：
- 团队咨询
- 协作学习
- 会议助手

### 8. 可解释性AI回答
**创新描述**：系统不仅提供答案，还能解释答案的来源、推理过程、置信度等信息，让用户更好地理解和信任AI的回答。

**技术实现**：
- 答案溯源追踪
- 推理路径展示
- 置信度评估

**应用场景**：
- 专业咨询（需要可信度）
- 教育场景（需要解释）
- 决策支持

## 项目反思与改进

### 当前阶段
项目核心功能已基本完成，包括：
- ✅ 文本对话功能（支持多轮对话、上下文管理）
- ✅ 语音对话功能（ASR和TTS基础功能，支持速度/音调调节）
- ✅ 角色管理功能（内置角色和自定义角色）
- ✅ RAG检索增强生成（文档上传、检索、增强生成）
- ✅ 用户界面（完整的Vue前端）
- ✅ 后端服务（Spring Boot完整实现）

### 潜在问题
1. **性能优化**：需要关注语音识别和合成的实时性能
2. **角色一致性**：确保不同角色在对话中保持风格一致性
3. **上下文管理**：多轮对话的上下文管理需要优化
4. **错误恢复**：需要完善的错误恢复机制
5. **资源消耗**：AI模型推理可能消耗大量计算资源
6. **RAG检索精度**：当前使用简单关键词匹配，可升级为向量数据库

### 改进方向
1. **RAG优化**：✅ 已完成基础RAG功能，可进一步优化检索准确性（集成专业向量数据库如Milvus、ChromaDB）
2. **缓存机制**：✅ 已实现对话缓存提升响应速度
3. **用户反馈**：✅ 已实现用户反馈机制持续优化
4. **语音功能增强**：✅ 已实现语音速度/音调调节，可进一步优化语音自然度
5. **多语言支持**：扩展多语言对话能力
6. **创新功能**：逐步实现上述创新点，提升竞争力
   - 智能数字人角色系统（AIGC+可视化）
   - 银河麒麟系统深度集成（国产化特色）
   - 联邦学习模型优化（隐私保护+持续优化）
   - 智能模型选择系统（最优性能+自适应）
7. **性能优化**：持续优化系统性能，降低资源消耗
8. **用户体验**：不断改进交互体验，提升用户满意度
9. **联邦学习**：利用联邦学习技术持续优化模型，保护用户隐私
10. **模型管理**：实现智能模型选择，平衡性能和资源消耗

---

## 最新更新（2024年）

### 用户画像和个性化推荐
已完成用户画像构建和个性化推荐功能：
- ✅ **用户画像服务**：`UserProfileService` - 收集和分析用户行为数据
  - 对话统计（总数、平均长度、消息数）
  - 角色使用分析（常用角色、使用频率）
  - 时间分布分析（活跃时段：早晨、下午、晚上、夜间）
  - 活跃度计算（非常活跃、活跃、中等、低活跃）
- ✅ **推荐服务**：`RecommendationService` - 基于用户画像提供个性化推荐
  - 角色推荐（常用角色、相似角色、热门角色）
  - 主题推荐（基于活跃度和角色偏好）
- ✅ **API接口**：`UserProfileController` - 提供画像查询和推荐接口

**使用方式**：
1. 获取用户画像：`GET /api/profile/{userId}`
2. 获取角色推荐：`GET /api/profile/{userId}/recommendations/roles?limit=5`
3. 获取主题推荐：`GET /api/profile/{userId}/recommendations/topics`
4. 更新用户偏好：`POST /api/profile/{userId}/preferences`

**技术实现**：
- 基于用户对话历史分析
- 智能推荐算法（基于使用频率、相似度）
- 实时画像构建（无需预先存储）

### 测试完善
已完成多个核心模块的单元测试：
- ✅ **RAG服务测试**：`RagServiceTest` - 测试RAG查询、文档列表、文档删除等功能
- ✅ **用户服务测试**：`UserServiceTest` - 测试用户创建、验证、密码更新等功能
- ✅ **密码工具测试**：`PasswordUtilTest` - 测试密码加密、验证等功能
- ✅ **认证控制器测试**：`AuthControllerTest` - 测试登录、注册、参数验证等功能

**测试覆盖**：
- RAG服务：查询、文档管理功能测试
- 用户认证：登录、注册、密码验证测试
- 密码加密：BCrypt加密和验证测试
- 错误处理：异常场景测试

**测试统计**：
- 新增测试类：4个
- 新增测试方法：30+个
- 测试覆盖率：从60%提升到约70%

### 数据库性能优化
已完成数据库索引优化：
- ✅ **索引优化脚本**：创建 `V2__optimize_indexes.sql` 数据库迁移脚本
- ✅ **用户表索引**：用户名、邮箱、创建时间索引
- ✅ **对话表索引**：用户ID、角色ID、上下文ID、更新时间索引（包括复合索引）
- ✅ **消息表索引**：对话ID、角色、类型、创建时间索引（包括复合索引）
- ✅ **角色表索引**：名称、创建时间索引
- ✅ **查询优化**：添加ANALYZE命令优化查询计划

**优化效果**：
- 用户查询性能提升
- 对话历史查询优化
- 消息检索速度提升
- 复合查询场景优化

### 用户认证完善
已完成用户认证功能完善：
- ✅ **密码加密**：实现 `PasswordUtil` 工具类，使用BCrypt算法加密密码
- ✅ **用户服务增强**：`UserService` 支持密码加密、验证、更新密码
- ✅ **登录验证**：`AuthController` 实现真正的密码验证登录
- ✅ **注册功能**：支持邮箱注册，自动密码加密
- ✅ **兼容性**：保持对旧数据（无密码用户）的兼容

**安全特性**：
- BCrypt密码加密（不可逆）
- 密码验证机制
- 用户名和邮箱唯一性检查
- 邮箱格式验证

### RAG功能实现
已完成RAG（检索增强生成）功能的完整实现：
- ✅ **文档处理服务**：支持txt、md格式文档解析，PDF/DOC格式需集成easydoc/mineru
- ✅ **知识库构建**：文档分块、关键词索引、持久化存储
- ✅ **文档检索**：基于关键词匹配和文本相似度的检索功能
- ✅ **增强生成**：将检索结果融入AI生成，提升回答准确性
- ✅ **API接口**：文档上传、查询、列表、删除等完整接口
- ✅ **对话集成**：ChatService支持可选的RAG增强模式

**使用方式**：
1. 上传文档到知识库：`POST /api/rag/documents`
2. 在对话中启用RAG：`POST /api/chat` 请求中设置 `useRag: true`
3. 直接RAG查询：`POST /api/rag/query`

**技术实现**：
- Python服务：`ai-service/app/services/rag_service.py` - RAG核心服务
- Python API：`ai-service/app/api/rag.py` - RAG API接口
- Java服务：`backend/src/main/java/com/kinlin/ai/service/RagService.java` - 后端RAG服务
- Java控制器：`backend/src/main/java/com/kinlin/ai/controller/RagController.java` - RAG控制器

**下一步优化**：
- 集成专业向量数据库（Milvus、ChromaDB等）提升检索精度
- 集成easydoc/mineru支持PDF、DOC等格式文档解析
- 优化检索算法，支持语义相似度搜索

---

### 用户反馈收集系统
已完成用户反馈收集和分析功能：
- ✅ **反馈实体**：`UserFeedback` - 支持多种反馈类型（质量、相关性、有用性等）
- ✅ **反馈服务**：`UserFeedbackService` - 收集、统计、分析用户反馈
  - 反馈提交和存储
  - 用户反馈统计（总数、平均评分、类型分布、情感分布）
  - 全局反馈统计
  - 自动情感分析（基于评分和内容关键词）
- ✅ **反馈API**：`UserFeedbackController` - 提供反馈提交和查询接口
- ✅ **数据库表**：`user_feedback` 表及索引优化

**使用方式**：
1. 提交反馈：`POST /api/feedback`
2. 获取用户反馈：`GET /api/feedback/user/{userId}`
3. 获取用户反馈统计：`GET /api/feedback/user/{userId}/statistics`
4. 获取全局统计：`GET /api/feedback/statistics`

**反馈类型**：
- quality（质量）
- relevance（相关性）
- helpfulness（有用性）
- other（其他）

### 告警机制
已完成系统监控和告警功能：
- ✅ **告警服务**：`AlertService` - 监控系统状态并触发告警
  - 错误率监控（阈值：10%）
  - 响应时间监控（阈值：5秒）
  - 请求速率监控（阈值：1000/秒）
- ✅ **告警API**：`AlertController` - 提供告警检查和查询接口
- ✅ **告警级别**：critical（严重）、warning（警告）、info（信息）
- ✅ **告警历史**：记录告警历史，支持查询

**使用方式**：
1. 手动触发告警检查：`POST /api/alerts/check`
2. 获取告警历史：`GET /api/alerts/history`
3. 获取指定类型告警：`GET /api/alerts/history/{alertType}`
4. 手动触发告警（测试）：`POST /api/alerts/trigger`

**告警规则**：
- 错误率 > 10% → warning级别告警
- 平均响应时间 > 5秒 → warning级别告警
- 请求速率 > 1000/秒 → info级别告警

---

### 语音速度/音调调节功能
已完成语音参数调节功能：
- ✅ **前端UI**：`VoiceChatView` - 添加语速和音调滑块控件
  - 语速调节（0.5x-2.0x，步长0.1）
  - 音调调节（0.5x-2.0x，步长0.1）
  - 实时参数显示
- ✅ **后端API**：`VoiceController` - 支持speed和pitch参数
- ✅ **AI服务**：`AIService`、`KylinSDKClient` - 支持参数传递和范围限制
- ✅ **参数验证**：自动限制参数范围（0.5-2.0）

**使用方式**：
1. 在语音对话界面，使用语速和音调滑块调节参数
2. 参数会实时应用到语音合成中
3. 参数范围：0.5x-2.0x

---

### 智能端导入错误修复 ✅ 新增
已完成智能端（Python AI服务）的导入错误修复：
- ✅ **修复类名不匹配问题**：创建 `KylinAIClient` 包装类，统一接口名称
  - `client.py` 中保留 `KylinSDKClient` 作为底层实现
  - 新增 `KylinAIClient` 包装类，自动从配置读取参数
  - 支持 `text` 和 `prompt` 两种参数名，提升兼容性
- ✅ **修复配置问题**：`KYLIN_AI_API_KEY` 改为可选，支持开发环境使用模拟响应
  - 配置文件中 `KYLIN_AI_API_KEY` 默认值为空字符串
  - 未设置 API key 时自动使用模拟响应，并记录警告日志
- ✅ **修复方法调用问题**：统一方法参数和返回值
  - `generate_text` 方法支持 `text` 和 `prompt` 参数
  - 返回值统一包含 `tokens_used` 字段
  - 修复 `chat.py` 中的响应字段映射问题
- ✅ **更新模块导出**：`__init__.py` 正确导出 `KylinAIClient` 和 `KylinSDKClient`

**修复内容**：
1. `agent/app/ai_engine/kylin_sdk/client.py` - 新增 `KylinAIClient` 包装类
2. `agent/app/ai_engine/kylin_sdk/__init__.py` - 更新导出
3. `agent/app/config.py` - 修复配置项默认值
4. `agent/app/api/chat.py` - 修复响应字段映射
5. `agent/app/services/ai_service.py` - 确保返回值包含所有必要字段

**使用说明**：
- 开发环境：可以不设置 `KYLIN_AI_API_KEY`，系统会自动使用模拟响应
- 生产环境：需要在 `.env` 文件或环境变量中设置 `KYLIN_AI_API_KEY`
- 导入方式：`from app.ai_engine.kylin_sdk.client import KylinAIClient`

---

**最后更新**：2024年

