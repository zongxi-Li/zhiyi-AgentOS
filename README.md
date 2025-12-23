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

### 🎨 全新设计系统 (2025 Refactor)

为了提供更具沉浸感和高级感的交互体验，我们全面重构了前端 UI/UX：

- **Kinlin Premium Design**: 采用 "Deep Space" 深色主题，营造专业、冷静的科技氛围。
- **现代化布局**: 
  - **侧边栏导航**: 更加符合专业工具的操作习惯，最大化内容展示区域。
  - **悬浮式输入框**: 玻璃拟态 (Glassmorphism) 设计，提升界面的通透感和层级感。
- **排版与字体**: 引入 `Inter` (无衬线) 和 `Noto Serif SC` (衬线) 字体组合，优化字间距和行高，确保极致的阅读体验。
- **细节打磨**: 去除冗余的装饰，强调微交互和细腻的边框光效。
- **语音交互升级**: 
  - **沉浸式语音空间**: 专为语音对话打造的深空背景，配合动态光球营造神秘氛围。
  - **可视化状态反馈**: 录音时的脉冲光环、思考时的流光效果，让 AI 的状态一目了然。
  - **悬浮控制台**: 极简的玻璃拟态控制面板，折叠次要参数，专注于对话体验。
  - **独立的角色创建页面**: 提供更加沉浸和详细的角色定制体验，支持分步骤引导和实时预览。
- **知识库与历史记录重塑**:
  - **RAG 知识库**: 采用全玻璃拟态设计，将复杂的文档管理和检索界面转化为通透、现代的仪表盘风格，并增加动态背景光效。
  - **智能历史归档**: 历史记录页面升级为时间轴式卡片流，支持通过颜色编码快速区分不同对话上下文，提供更愉悦的回溯体验。

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
