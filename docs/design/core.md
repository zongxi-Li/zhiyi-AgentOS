知弈系统层次架构

> 本文按“驾驭工程”视角重新组织系统：重点不是单次回答，而是围绕智能体建立可编排、可接管、可回放、可观测的运行时。

一、总体架构层次

前端 (Frontend / Console)
    │
    ├── HTTP / WebSocket
    │
Java后端 (业务中枢 / 统一网关)
    │
    ├── REST API / WebSocket
    │
Python智能体服务 (编排运行时 / 控制平面)
    │
    ├── HTTP / SDK
    │
外部AI服务 (DeepSeek / Qwen / OpenAI / 麒麟)


二、Java后端分层架构 (MVC+)

2.1 接入层

┌─────────────────────────────────────┐
│            Controller 层            │
├─────────────────────────────────────┤
│ • AuthController        (鉴权)      │
│ • ChatController        (聊天)      │
│ • ConversationController(会话)      │
│ • RoleController        (角色)      │
│ • AgentController       (智能体代理)│
│ • RagController         (RAG)       │
│ • RecommendationController(推荐)    │
│ • FileController        (文件)      │
│ • 其他 15+ 功能控制器               │
└─────────────────────────────────────┘
           │
           ▼

2.2 业务层

┌─────────────────────────────────────┐
│             Service 层              │
├─────────────────────────────────────┤
│ 主业务服务                          │
│  • ChatService         (聊天核心)   │
│  • ConversationService (会话管理)   │
│  • RoleService         (角色管理)   │
│  • UserService         (用户管理)   │
├─────────────────────────────────────┤
│ Python 服务网关                     │
│  • AiService           (AI 聊天网关)│
│  • RagService          (RAG 网关)   │
│  • AgentGatewayService (智能体网关) │
├─────────────────────────────────────┤
│ AI 功能服务                         │
│  • RecommendationService (推荐)     │
│  • DigitalHumanService  (数字人)    │
│  • EmotionAwareService  (情感)      │
│  • KnowledgeGraphService(知识图谱)  │
├─────────────────────────────────────┤
│ 基础设施服务                        │
│  • CacheService        (缓存)       │
│  • MetricsService      (指标)       │
│  • FileService         (文件存储)   │
└─────────────────────────────────────┘
           │
           ▼

2.3 数据访问层

┌─────────────────────────────────────┐
│           Repository 层             │
├─────────────────────────────────────┤
│ • UserRepository        (用户)      │
│ • RoleRepository        (角色)      │
│ • ConversationRepository(会话)      │
│ • MessageRepository     (消息)      │
│ • UserFeedbackRepository(反馈)      │
└─────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│             Entity 层               │
├─────────────────────────────────────┤
│ User                                │
│   ├── id, username, email, ...      │
│   └── 1:N → Role                    │
│                                      │
│ Role                                │
│   ├── id, name, roleType, ...       │
│   └── 1:N → Conversation            │
│                                      │
│ Conversation                        │
│   ├── id, userId, roleId, ...       │
│   └── 1:N → Message                 │
│                                      │
│ Message                             │
│   ├── conversationId, role, content │
│   └── messageType, metadata         │
│                                      │
│ UserFeedback                        │
│   └── 关联 User / Conversation / Message │
└─────────────────────────────────────┘

2.4 横切关注点

┌─────────────────────────────────────┐
│        Config / Filter / ...        │
├─────────────────────────────────────┤
│ • SecurityConfig      (安全配置)    │
│ • JwtAuthenticationFilter (JWT 过滤)│
│ • WebClientConfig     (HTTP 客户端) │
│ • GlobalExceptionHandler(异常处理)  │
│ • LoggingAspect       (日志切面)    │
│ • MetricsAspect       (指标切面)    │
│ • RateLimitInterceptor(限流拦截)    │
└─────────────────────────────────────┘

2.5 Java 后端在整体中的定位

Java 后端仍然是系统的业务中枢，负责：

- 用户、角色、会话、消息、反馈、推荐等主业务状态。
- 对 Python 智能体服务的统一访问入口。
- 对前端暴露稳定 API，并承担持久化和鉴权。
- 为控制台和工作台保留可查询、可审计的业务记录。


三、Python智能体服务分层架构

3.1 驾驭工程定位

这里的“驾驭工程”不是把模型包一层 HTTP，而是围绕智能体建立一套可控运行时。它要解决四件事：

- 编排：把用户意图拆成任务流，而不是一次性 prompt。
- 控制：让系统支持接管、恢复、降级和回放。
- 观测：让每一步都有 trace、状态和结果。
- 治理：让错误、风险、限流、联邦增强都处于可管理边界内。

换句话说，Python 层不只是“AI 引擎”，而是“智能体控制平面 + 执行平面”。

3.2 控制平面（Control Plane）

┌─────────────────────────────────────┐
│             API 路由层              │
├─────────────────────────────────────┤
│ 核心 API                            │
│  • /ai/chat/*        (聊天接口)     │
│  • /ai/agent/*/chat  (专业体入口)   │
│  • /rag/*            (RAG 接口)     │
│  • /ai/tts           (语音合成)     │
├─────────────────────────────────────┤
│ 扩展 API                            │
│  • /ai/digital-human/* (数字人)     │
│  • /ai/emotion/*      (情感分析)    │
│  • /api/knowledge-graph/*(知识图谱)│
│  • /ai/federated-*    (联邦能力)    │
│  • /ai/voice/*        (语音)        │
│  • /ai/aigc/*         (AIGC)        │
└─────────────────────────────────────┘

这一层负责：

- 接收 Java 后端转发的请求。
- 校验参数、整理 `session_id`、角色和上下文。
- 把请求送入编排运行时。
- 返回结构化结果，而不是只返回自然语言文本。

它本质上是控制台的服务端入口。

3.3 编排平面（Orchestration）

┌─────────────────────────────────────┐
│            编排核心层               │
├─────────────────────────────────────┤
│ Schema 层 (agent_core/schema/)      │
│  • PlannedAction                    │
│  • SkillRequest / SkillResult       │
│  • AgentTraceStep                   │
│  • Agent*Request / Agent*Response   │
├─────────────────────────────────────┤
│ 规划执行层 (agent_core/react/)      │
│  • ReactPlanner     (意图拆解/规划) │
│  • ReactExecutor    (逐步执行/汇总) │
│  • ToolRouter       (动作到技能映射) │
├─────────────────────────────────────┤
│ 任务状态层                          │
│  • session_id                       │
│  • history                          │
│  • observations                     │
│  • trace / skills_used              │
│  • risk_level / federated           │
└─────────────────────────────────────┘

这层的核心运行方式是：

`request -> plan -> execute -> observe -> summarize -> respond`

其中：

- `ReactPlanner` 负责把意图转成 `PlannedAction` 序列。
- `ReactExecutor` 负责逐步调用技能，并把观测结果写回 memory。
- `ToolRouter` 负责把动作名映射到具体 skill。
- `AgentTraceStep` 负责记录每一步的 thought / action / observation。

3.4 任务流与状态

当前代码已经具备最小可用的任务流骨架：

- `session_memory_store`：保存短期会话历史。
- `history`：作为规划和技能执行的上下文。
- `observations`：保存每一步技能输出，供后续步骤消费。
- `skills_used`：记录本轮调用过哪些能力。
- `trace`：返回给前端和后端，用于审计、回放和控制台渲染。

建议把后续状态机统一为：

`idle -> planning -> running -> reviewing -> completed`

失败路径统一为：

`failed -> retrying -> recovered / fallback`

这样控制台、恢复、重试、人工接管才能共享同一套语义。

3.5 能力执行平面

┌─────────────────────────────────────┐
│            能力执行层               │
├─────────────────────────────────────┤
│ 技能库 (agent_core/skills/)         │
│  • 律师技能                         │
│  • 教师技能                         │
│  • 程序员技能                       │
│  • 作家技能                         │
├─────────────────────────────────────┤
│ 检索层 (agent_core/retrieval/)      │
│  • 法律/教育/代码索引构建器          │
│  • Chroma 向量客户端                 │
├─────────────────────────────────────┤
│ 联邦适配 (agent_core/federated/)    │
│  • FederatedAdapter                 │
├─────────────────────────────────────┤
│ 服务层 (app/services/)              │
│  • AIService / RagService           │
│  • Emotion / Voice / DigitalHuman   │
│  • Federated / Performance / KG     │
├─────────────────────────────────────┤
│ 模型适配层 (ai_engine/)             │
│  • DeepSeekAdapter                  │
│  • QwenAdapter                      │
│  • SpeechAdapter                    │
│  • MultimodalAdapter                │
│  • KylinAIClient                    │
└─────────────────────────────────────┘

这一层负责“真正做事”：

- 技能执行具体专业动作。
- 检索层提供知识和向量上下文。
- 联邦层对推荐、判断或结果进行增强。
- AI 引擎层封装外部模型调用。

上层决定“做什么、先后顺序、何时停”；这一层决定“具体怎么做”。

3.6 可观测性与治理平面

┌─────────────────────────────────────┐
│          观测与治理层               │
├─────────────────────────────────────┤
│  • logger / logging                 │
│  • errorhandler                     │
│  • ratelimit                        │
│  • performance monitor / optimizer  │
│  • trace / skills_used / federated  │
│  • risk_level / message / error     │
└─────────────────────────────────────┘

这层不是附属能力，而是驾驭工程的核心：

- 没有 trace，就没有控制台。
- 没有风险字段，就没有治理边界。
- 没有统一错误语义，就无法恢复和降级。
- 没有性能观测，就无法支撑长任务和多智能体协作。

3.7 数据与资源层

┌─────────────────────────────────────┐
│            数据资源层               │
├─────────────────────────────────────┤
│ 领域知识库 (app/data/)             │
│  • legal/                           │
│  • education/                       │
│  • rag/                             │
├─────────────────────────────────────┤
│ 提示词模板 (app/prompts/)           │
│  • 各专业体提示词文件               │
├─────────────────────────────────────┤
│ 静态资源 (app/static/)              │
│  • 数字人资源                       │
└─────────────────────────────────────┘

3.8 Python 智能体服务在整体中的定位

这一层已经不应被理解为“Python 版后端”，而应被理解为：

- 智能体运行时。
- 任务编排器。
- 技能执行器。
- 控制台所依赖的观测来源。
- 联邦增强与专业能力的统一承载层。


四、关键调用链路层次

4.1 普通聊天链路

前端
  │ HTTP POST /chat/text
  ▼
Java Controller 层
  │ ChatController.sendTextMessage()
  ▼
Java Service 层
  │ ChatService.sendMessage()
  ├── 会话 / 消息持久化
  ├── 可选 RAG 增强
  ├── RoleSwitchOptimizer(角色上下文)
  └── AiService.sendTextMessage()
        │ WebClient → Python
        ▼
Python 控制平面
  │ /ai/chat/text
  ▼
Python 执行层
  │ AIService.generate_text()
  ▼
模型适配层
  │ KylinAIClient → DeepSeek / Qwen
  ▼
AI 响应返回 ←──┐
              │
Java 持久化 AI 回复
              │
返回前端响应 ←─┘

这条链路仍以“单轮生成”为主，驾驭工程属性较弱，主要由 Java 侧负责会话和业务状态。

4.2 专业体智能体链路

前端 / Workbench
  │ HTTP POST /api/agent/{role}/chat
  ▼
Java AgentController
  │ AgentGatewayService.callAgent()
  ▼
Python 专业体 API
  │ /ai/agent/{role}/chat
  ├── session_memory_store(会话历史)
  ├── ReactPlanner.plan()     (任务拆解)
  ├── ReactExecutor.execute() (逐步执行)
  └── ToolRouter -> 具体 Skill
        │
        ▼
能力执行层
  ├── 领域知识检索
  ├── 联邦增强调用(可选)
  ├── LLM 综合生成
  └── trace / skills_used / observations 收集
        │
        ▼
返回结构化结果 ←──┐
  • answer        │
  • skillsUsed    │
  • trace         │
  • federated     │
  • riskLevel     │
  • 专业体字段    │
                  │
Java 持久化会话与消息 ←──┘
                  │
前端控制台 / 工作台渲染 ←─┘

这条链路是当前系统最接近“驾驭工程”的部分，因为它已经具备：

- 规划
- 步骤执行
- 结构化返回
- trace 可视化基础

4.3 控制台观测链路

前端控制台 / Workbench
  │ 展示 trace、skillsUsed、riskLevel、federated
  ▼
Java 后端查询会话与消息
  ▼
Python 返回结构化结果与步骤日志
  ▼
用于回放、接管、重试、分析

这里的关键点是：控制台不是“再做一个页面”，而是把现有结构化结果真正作为运维和协作界面使用起来。

4.4 数据持久化层次

Java 实体层
  │ User → Role → Conversation → Message
  │                    ▲
  └── UserFeedback ────┘
        │
        ▼
JPA Repository
        │
        ▼
数据库 (PostgreSQL / H2)
        │
        ▼
Flyway 迁移
  │ V1__init_schema.sql
  │ V2__optimize_indexes.sql
  └── ...


五、模块耦合关系

          前端
           │
    HTTP / WebSocket
           │
    ┌──────┴──────┐
    │             │
Java后端        Python智能体
(业务+持久化)    (编排+技能+观测)
    │             │
    └──────┬──────┘
           │
       外部AI服务
   (DeepSeek / Qwen / ...)

耦合边界应保持为：

- Java 负责业务实体、鉴权、会话、推荐和统一接入。
- Python 负责编排、执行、联邦增强和观测。
- 前端通过 Chat、RAG、Workbench 三个入口消费业务结果与运行时结果。


六、部署单元

单元1: Java后端服务
  ├── Spring Boot 应用
  ├── 端口: 5000(dev) / 8080(prod)
  └── 依赖: DB, Redis

单元2: Python智能体服务
  ├── FastAPI 应用
  ├── 端口: 8000 / 9000
  └── 依赖: AI APIs, 向量 DB

单元3: 前端应用
  ├── Web 应用
  └── 代理到后端服务


七、驾驭工程落地原则

- 智能体不是黑盒，必须输出结构化 trace。
- 编排不是 prompt 拼接，必须有显式状态和步骤。
- 控制台不是展示层附属件，而是运行时的一部分。
- 可观测性优先于复杂能力扩张，先把失败看清楚，再谈放大能力。
- 联邦能力优先服务于推荐、调度和评估，不先碰大规模训练。


在这个蓝图下，用户体验不能再是“打开聊天框问一句”，而应该是“发起一个专业任务，系统把它变成可控工作流”。也就是说，用户看到的是工作台、任务流、Agent 状态、审核节点和最终交付物；聊天只是入口之一。

**用户使用流程**

最典型的流程是这样：

1. 用户进入系统，选择场景  
   例如：法律分析、合同审查、教学方案、代码审查、写作规划。MVP 阶段建议先只开放“法律工作流”。

2. 用户发起任务  
   可以从 `Chat` 输入自然语言，也可以从 `Workbench` 直接选择模板。  
   例如：“帮我分析一个合同纠纷案件，判断风险并生成初步文书。”

3. 系统把聊天意图升级为 Workflow  
   Orchestrator 判断这不是普通问答，而是一个法律任务，于是生成任务计划：案件拆解、法条检索、类案分析、证据分析、风险评估、文书生成、审查。

4. 用户补充结构化材料  
   系统要求用户填写或上传：案情描述、合同文本、证据材料、诉求、地区、时间节点。  
   这里开始从“聊天”进入“专业工作流”。

5. Orchestrator 展示执行计划  
   用户看到每一步由哪个 Agent 执行、预计产出什么、哪些步骤需要人工确认。  
   例如：`CaseIntakeAgent -> StatuteAgent -> EvidenceAgent -> RiskAgent -> DraftingAgent -> ReviewAgent`。

6. 多 Agent 执行任务  
   每个 Agent 只负责自己的专业环节。用户可以看到状态：运行中、等待审核、失败、重试、已完成。  
   这就是“驾驭工程”的核心：用户不是等一个黑盒回答，而是在控制一个任务系统。

7. 人工审核关键节点  
   例如风险评估完成后，系统要求用户确认是否继续生成文书。用户可以通过、驳回、要求重跑、补充材料。

8. 系统生成最终交付物  
   输出不只是回答，而是完整专业成果：案情摘要、争议焦点、法律依据、风险清单、文书草稿、审查意见。

9. 系统沉淀记忆和评估  
   用户是否采用结果、修改了哪里、哪个 Agent 出错、哪个步骤恢复成功，都会进入评估体系。私有数据留在本地，联邦层只学习匿名模式。

**面向用户群体**

第一优先级不是普通 C 端用户，而是“有专业任务、需要可控流程、不能完全信任黑盒回答”的职业用户。

核心用户建议分三层：

- 主要用户：法律从业者、企业法务、合同审查人员、政企法律事务人员。他们需要的是案件分析、合同审查、风险评估、文书生成和可追溯审核。

- 次要用户：学校教师、教研人员、培训机构老师。他们适合后续扩展到教学诊断、教案生成、作业批改、学习路径规划。

- 后续用户：程序员、技术负责人、写作者、内容团队。他们可以使用代码审查、需求拆解、架构建议、写作大纲、内容审校等职业工作流。

在组织里还会有不同角色：

- 执行者：日常发起任务的人，比如律师助理、法务专员、教师、工程师。

- 审核者：对结果负责的人，比如律师、法务负责人、教研负责人、技术负责人。

- 管理者：关心效率、合规、审计和团队产出的人。

- 知识维护者：维护本地知识库、案例库、模板库、规则库的人。

所以最清晰的产品定位应该是：

```text
不是大众聊天助手，
而是给专业组织使用的可治理职业 Agent 工作流平台。
```

第一版最建议聚焦：

```text
企业法务 / 律所 / 政企法律事务部门
  -> 合同纠纷与合同审查工作流
  -> 可追踪、可恢复、可审核、可评估
```

这样用户流程、技术架构和商业对象是对齐的。


你的判断是对的：如果要做出差异化，主流目标确实更应该落在国产操作系统 / 信创环境下的政府、金融、教育、医疗、央国企这些信息敏感领域。这里的用户痛点不是“有没有一个聊天机器人”，而是“数据不能出域、流程要可审计、结果要可追责、部署要适配国产软硬件”。

我查了一下当前外部情况，国产操作系统和信创方案确实主要覆盖政府、金融、能源、教育、医疗等关键行业；金融、央国企、政务也在加速私有化大模型部署。与此同时，Agent 平台赛道已经很热，Dify、Coze、FastGPT、LangGraph、CrewAI、AutoGen 等都在做低代码、工作流、多 Agent 或私有部署。所以结论不是“没有市场”，而是“通用 Agent 平台市场已经拥挤，敏感行业里的可治理、可私有化、可国产化适配 AgentOS 还有空间”。

我会这样重新定位：

```text
不是：通用 AI 聊天软件
不是：又一个 Dify / Coze / Flowise
而是：信创环境下的可治理职业智能体操作系统
```

更准确一点：

```text
知弈 AgentOS
面向政府、金融、教育、医疗、央国企的私有化职业智能体工作流底座
```

**通用软件有没有优势？**

有，但不能做成“面向所有人的通用 AI 工具”。那样会直接撞上 Dify、Coze、FastGPT、LangGraph、OpenHands、企业 Copilot，优势不明显。

真正可行的是做“通用底座 + 行业插件”的公约数产品。

也就是：

```text
通用底座：
Orchestrator + Agent 状态机 + 工作流控制台 + 记忆系统 + 权限审计 + 可观测性 + 联邦经验

行业包：
政务包 / 金融包 / 教育包 / 医疗包 / 法律包
```

这样你不是每个行业都从零做，而是用同一套 AgentOS 架构辐射各行各业。每个行业只替换知识库、工作流模板、专业 Agent、审查规则和数据连接器。

**最好的产品形态**

我建议你采用“两层产品”：

```text
第一层：知弈 AgentOS Core
通用智能体操作系统底座

第二层：Industry Workflow Packs
行业职业工作流包
```

Core 负责公约数能力：

- 多 Agent 编排
- 状态机
- Checkpoint 恢复
- Trace 可观测
- 人工审核
- 权限与审计
- 私有化部署
- 国产 OS / 信创适配
- 联邦经验学习
- 工作流级评估

行业包负责垂直能力：

- 政务：政策问答、公文生成、材料审核、办事流程辅助
- 金融：合规审查、风控报告、投研摘要、客户材料审核
- 教育：教案、学情分析、作业批改、教学评估
- 医疗：病历结构化、质控、科研文献、院内知识助手，先别碰自动诊断
- 法律：合同审查、案件分析、法条检索、风险评估、文书生成

**为什么这个方向更有优势**

你的优势不应该是“我也能搭 Agent”，而是：

```text
我能在国产化、私有化、高敏数据环境里，让 Agent 可控、可审计、可恢复、可评估地完成专业流程。
```

这是通用 Agent 平台不一定天然重视的地方。它们更偏开发效率、低代码搭建、模型连接、知识库应用。你的差异点应该放在：

- 信创适配
- 私有化部署
- 敏感数据不出域
- 职业工作流
- Agent 治理
- 审计追踪
- 状态恢复
- 联邦经验共享

**科研方向也成立**

而且这个方向很适合科研，不一定非要做纯算法。你可以做“系统型研究”。

比较好的题目方向：

```text
面向信创环境的可治理多智能体操作系统架构

面向敏感行业的状态驱动职业 Agent 工作流框架

基于 Checkpoint 的长任务多 Agent 恢复机制

联邦记忆增强的职业多智能体协作系统

面向政企私有化部署的 Agent Workflow Evaluation 体系
```

核心创新点不是“模型更聪明”，而是“Agent 更稳定、更可控、更适合敏感行业长流程”。

**我的建议**

可以做公约数产品，但不要叫“通用 Agent 平台”。这个名字太容易被竞品吞掉。

更好的主线是：

```text
信创环境下的职业智能体操作系统
```

商业入口先打：

```text
政府 / 央国企 / 金融 / 教育 / 医疗的信息敏感场景
```

技术内核做：

```text
可治理多 Agent 工作流底座
```

科研表达做：

```text
Stateful Governed Professional Multi-Agent Operating Platform
```

这样产品、技术、科研三条线是统一的，不会互相拉扯。

参考来源：国产 OS / 信创行业覆盖与关键行业落地可参考统信、麒麟与信创方案介绍；企业私有化 AI 部署趋势可参考德勤中国和证券时报相关报道；Agent 平台竞争格局可参考 Dify、Coze、FastGPT、CrewAI、AutoGen、LangGraph 等横评资料。  
来源链接：[国产操作系统关键行业应用](https://www.eefocus.com/article/1989910.html)、[AICOS 信创与政府企业平台](https://www.huilan.com/web/cp/jsdz/aicdsznzhddxt/index.shtml)、[金融大模型私有化部署](https://www.stcn.com/article/detail/1026873.html)、[Dify/Coze/FastGPT 横评](https://www.53ai.com/news/LargeLanguageModel/2025062095378.html)、[企业级多智能体平台选型](https://www.betteryeah.com/blog/2026-enterprise-multi-agent-platform-selection-guide)


不太合适。准确说：**核心底座不能硬编码行业 Agent 和工作流**，但 **Skill/Tool 的具体实现可以是代码**。这两者要分开。

你现在担心的是对的。如果把 `LawyerAgent`、`TeacherAgent`、`case_intake_agent.py`、`statute_agent.py` 这些都直接写进 Core 的调度逻辑里，短期容易跑通，长期会变成：

- 每加一个行业，都要改 Core。
- 每加一个 Agent，都要改 Orchestrator。
- 每改一个流程，都要发版。
- 政务、金融、教育、医疗会互相污染。
- Core 不再是操作系统底座，而变成行业代码大杂烩。

更好的方案是：**Core 只提供运行时，行业能力通过 Pack 注册进来。**

**推荐方案：配置驱动 + 插件注册**

核心思想：

```text
Core 不认识具体行业
Core 只认识 Task / Workflow / Agent / Tool / State / Trace / Checkpoint

行业包自己声明：
我有哪些 Agent
我有哪些 Workflow
每个 Workflow 有哪些 Step
每个 Step 用哪个 Agent
每个 Agent 能调用哪些 Tool
```

也就是：

```text
知弈 AgentOS Core
	负责运行、调度、状态、恢复、观测、审核、评估

Industry Workflow Pack
	负责行业 Agent、行业流程、行业知识、行业工具、行业规则
```

**哪些应该写代码，哪些不该写死**

| 内容 | 是否硬编码 | 原因 |
|---|---:|---|
| `BaseAgent` 接口 | 可以代码化 | 这是稳定抽象 |
| `WorkflowRuntime` | 可以代码化 | Core 的运行时能力 |
| `StateMachine` | 可以代码化 | 全系统统一规则 |
| `Checkpoint` | 可以代码化 | 通用恢复机制 |
| `TraceEvent` | 可以代码化 | 通用观测机制 |
| 具体行业 Agent 列表 | 不应写死 | 应由行业包注册 |
| 具体工作流步骤 | 不应写死 | 应由配置声明 |
| Agent 可调用哪些 Skill | 不应写死 | 应由 Agent manifest 声明 |
| 行业知识库路径 | 不应写死 | 应由 pack 配置 |
| 审核节点规则 | 不应写死 | 应由 workflow 配置 |

**建议的结构**

```text
agent/
	app/
		agent_core/
			orchestration/
				orchestrator.py
					只负责读取 WorkflowDefinition，然后按步骤调度，不关心具体行业。

				workflow_registry.py
					加载所有行业包里的 workflow.yaml / workflow.json。

				agent_registry.py
					加载所有行业包里的 agent.yaml / agent.json，并绑定到实际 Agent 类。

				tool_registry.py
					注册所有可调用工具，供 Agent 使用。

				state_machine.py
					统一状态流转。

				checkpoint.py
					统一恢复机制。

				trace.py
					统一执行轨迹。

			agents/
				base.py
					定义 BaseAgent，不放具体行业逻辑。

			packs/
				legal/
					pack.yaml
						声明法律行业包基本信息。

					agents.yaml
						声明 CaseIntakeAgent、StatuteAgent、EvidenceAgent 等 Agent。

					workflows/
						contract_review.yaml
							声明合同审查工作流步骤。

						case_analysis.yaml
							声明案件分析工作流步骤。

					agents/
						case_intake.py
							实现案情接收 Agent。

						statute.py
							实现法条 Agent。

					skills/
						legal_search.py
							实现法律检索工具。

					prompts/
						case_intake.md
							该 Agent 使用的提示词模板。

				education/
					pack.yaml
					agents.yaml
					workflows/
					agents/
					skills/
					prompts/

				finance/
					pack.yaml
					agents.yaml
					workflows/
					agents/
					skills/
					prompts/
```

**一个 workflow 配置可以长这样**

```yaml
id: legal_contract_review
name: 合同审查工作流
domain: legal
version: 1.0.0

steps:
  - id: intake
    name: 材料接收
    agent: case_intake
    next: statute

  - id: statute
    name: 法条检索
    agent: statute
    next: risk

  - id: risk
    name: 风险评估
    agent: risk
    review: true
    next: draft

  - id: draft
    name: 文书草拟
    agent: draft
    next: final_review

  - id: final_review
    name: 最终审查
    agent: review
    review: true
    next: done
```

这样 Orchestrator 不需要知道“合同审查到底有哪些步骤”，它只需要按配置执行：

```text
读取 workflow
	-> 找到 step
	-> 根据 agent 名称从 registry 取 Agent
	-> 执行 Agent
	-> 写 trace
	-> 写 checkpoint
	-> 判断是否 review
	-> 推进下一步
```

**一个 agent 配置可以长这样**

```yaml
id: risk
name: 风险评估 Agent
domain: legal
class: packs.legal.agents.risk.RiskAgent

capabilities:
  - risk_assessment
  - limitation_check
  - jurisdiction_check

tools:
  - risk_assessment_skill
  - limitation_calculation_skill
  - jurisdiction_determination_skill

memory:
  read:
    - workflow
    - career
  write:
    - workflow

review_required: false
```

这样 Agent 的能力边界、工具权限、记忆权限都可以配置，不需要写死在 Orchestrator 里。

**我建议采用的最终模型**

```text
1. Core Runtime
	稳定代码，不碰行业逻辑。

2. Registry System
	负责加载 Agent、Tool、Workflow、Pack。

3. Pack Manifest
	每个行业包用配置声明自己有什么。

4. Agent Class
	行业 Agent 是代码，但通过配置注册，不被 Core 直接 import。

5. Workflow DSL
	工作流用 YAML / JSON 声明，支持版本化。

6. Tool Contract
	Skill 是代码实现，但必须暴露统一 schema。

7. Policy Layer
	审核、权限、记忆、风险等级用配置控制。
```

**关键优化点**

你现在不要让目录变成：

```text
agent_lawyer.py
agent_teacher.py
agent_programmer.py
agent_writer.py
```

这种方式会把职业写死。

更好的方向是：

```text
packs/legal/
packs/education/
packs/finance/
packs/medical/
packs/government/
```

每个 pack 自己注册：

```text
agents
workflows
tools
prompts
knowledge
policies
metrics
```

Core 只提供：

```text
load_pack()
register_agent()
register_workflow()
run_workflow()
resume_workflow()
review_step()
evaluate_run()
```

**结论**

你的判断是对的，硬编码职业智能体会限制扩展性。最优方案不是完全不写代码，而是：

```text
Core 代码化
行业配置化
Agent 插件化
Workflow 声明化
Skill 工具化
Policy 策略化
```

这样“知弈 AgentOS Core”才真正像操作系统底座，而不是一组固定 Agent 的集合。行业包可以不断扩展，但 Core 不需要频繁改动。
