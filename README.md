# 知弈 — 职业智能体操作系统

## 项目概述

知弈是一个面向信创与信息敏感行业的职业智能体操作系统。系统采用 **前端(Vue 3) + 后端(Spring Boot) + AI服务(Python FastAPI + AgentOS)** 三层架构，支持律师、教师、程序员、作家四种专业 Agent 角色，具备 ReAct 自主规划执行、技能调用、知识检索、流式对话、联邦学习等核心能力。AI 引擎采用 DeepSeek + 通义千问双引擎，文本生成由 DeepSeek 主力驱动。

### 核心特性

- **AgentOS 工作流运行时**: 自研 WorkflowRuntime + Orchestrator 编排引擎，支持 Task 管理、步骤进度追踪、Checkpoint 恢复、人工审核、治理指标
- **多 Agent 角色系统**: 律师/教师/程序员/作家四种专业 Agent，支持无缝切换，每种 Agent 拥有独立的 Skill 面板和视觉风格（蓝/绿/紫/琥珀四色主题）
- **ReAct 推理引擎**: 基于 Thought-Action-Observation 循环的自主规划执行，可观测、可追踪
- **LangGraph 合同审查**: 律师合同审查迁移至 LangGraph 状态图，支持证据面板、风险面板、审查报告预览
- **流式对话 (SSE)**: DeepSeek 主力驱动的文本生成，支持 Server-Sent Events 实时逐字输出
- **双 AI 引擎**: DeepSeek（文本主引擎）+ 通义千问（图像/语音/多模态），LLM Gateway 统一路由与回退
- **知识检索增强 (RAG)**: ChromaDB 向量数据库 + 关键词/向量混合检索，支持法条/判例/教育知识检索
- **联邦学习优化**: 隐私保护的模型持续优化，联邦学习全局最优模型系统
- **数字人系统**: AIGC 生成数字人形象，实时语音驱动，多风格切换
- **多语言支持**: 简体中文/英文切换，vue-i18n 国际化

## 技术栈

### 前端

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue | 3.3.4 | 前端框架 |
| TypeScript | 5.4.5 | 类型安全 |
| Vite | 5.0.0 | 构建工具 |
| Element Plus | 2.4.4 | UI 组件库 |
| Pinia | 2.1.7 | 状态管理 |
| Vue Router | 4.2.5 | 路由管理 |
| vue-i18n | 9.14.5 | 国际化 |
| Axios | 1.6.2 | HTTP 客户端 |
| Sass | 1.97.1 | CSS 预处理器 |

### 后端

| 技术 | 版本 | 用途 |
|------|------|------|
| Java | 17 | 编程语言 |
| Spring Boot | 3.2.0 | 应用框架 |
| Spring Data JPA | — | 数据持久化 |
| Spring Data Redis | — | 缓存 |
| Spring Validation | — | 参数校验 |
| PostgreSQL | 15 | 关系数据库 |
| Redis | 7 | 缓存/会话 |
| JWT | — | 认证授权 |
| MapStruct | — | 对象映射 |

### AI 服务 & AgentOS

| 技术 | 用途 |
|------|------|
| Python 3.9+ | 编程语言 |
| FastAPI + Uvicorn | Web 框架与 ASGI 服务器 |
| LangGraph | 合同审查状态图编排 |
| OpenAI SDK | DeepSeek + 通义千问兼容调用 |
| DashScope SDK | 阿里云 AI 服务（语音/图像/多模态） |
| ChromaDB | 向量数据库 |
| sentence-transformers | 文本嵌入 |
| PyPDF2 / pdfplumber | PDF 解析 |
| python-docx / openpyxl | 文档解析 |

### 基础设施

| 技术 | 用途 |
|------|------|
| Docker + Docker Compose | 容器化开发与部署 |
| Nginx | 反向代理/静态资源 |

## 系统架构

```
┌──────────────────────────────────────────────────────────────┐
│                    用户交互层 (Frontend)                       │
│   Vue 3 + TypeScript + Element Plus + Pinia                  │
│   ┌───────┐ ┌──────────┐ ┌───────┐ ┌───────┐ ┌──────────┐  │
│   │ 对话  │ │ 合同审查  │ │ 数字  │ │ 知识  │ │ 联邦学习 │  │
│   │ 界面  │ │ 工作台    │ │  人   │ │  库   │ │ 工作台   │  │
│   └───────┘ └──────────┘ └───────┘ └───────┘ └──────────┘  │
└──────────────────────┬───────────────────────────────────────┘
                       │ HTTP/SSE
                       ▼
┌──────────────────────────────────────────────────────────────┐
│                  业务网关层 (Backend)                          │
│   Spring Boot 3.2 + Java 17 + JWT + Redis                   │
│   ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────────┐        │
│   │ 认证 │ │ 对话 │ │ 角色 │ │ 文件 │ │ AgentOS  │        │
│   │ 授权 │ │ 处理 │ │ 管理 │ │ 管理 │ │ 网关     │        │
│   └──────┘ └──────┘ └──────┘ └──────┘ └──────────┘        │
│   PostgreSQL + Redis                                         │
└──────────────────────┬───────────────────────────────────────┘
                       │ HTTP (REST API)
                       ▼
┌──────────────────────────────────────────────────────────────┐
│              AI 引擎 & AgentOS 层 (Python)                    │
│   FastAPI + LangGraph + ChromaDB                             │
│   ┌──────────────────────────────────────────────┐          │
│   │        AgentOS Workflow Runtime              │          │
│   │  TaskManager → Orchestrator → Pack Agent     │          │
│   │  Domain Models (Task/Step/Agent/Workflow)    │          │
│   │  Progress Tracking + Checkpoint + Review     │          │
│   └──────────┬───────────────────────────────────┘          │
│              │ Skill 调用                                     │
│   ┌─────────┴──────────────────────────────────┐           │
│   │ 律师 Pack   │ 教师 Pack  │ 程序员 │ 作家   │           │
│   │ 案情理解    │ 学生诊断   │ 代码   │ 大纲   │           │
│   │ 法条检索    │ 教案生成   │ 审查   │ 风格   │           │
│   │ 判例检索    │ 作业批改   │ 调试   │ 分析   │           │
│   │ 文书生成    │ 错因推送   │ 架构   │ 情节   │           │
│   │ 合同审查    │ 学习路径   │ 测试   │ 润色   │           │
│   └───────────────────────────────────────────┘           │
│   LLM Gateway → DeepSeek / Qwen                            │
│   RAG → ChromaDB + Keyword Retriever                       │
└──────────────────────────────────────────────────────────────┘
```

## 项目结构

```
kinlin_ai/
├── frontend/                          # 前端项目 (Vue 3 + TypeScript + Vite)
│   ├── src/
│   │   ├── views/                     # 页面组件
│   │   │   ├── ChatView.vue              # 对话主页面（Agent 切换 + 流式输出）
│   │   │   ├── LawyerContractReviewWorkbenchView.vue  # 律师合同审查工作台
│   │   │   ├── FederatedAgentWorkbenchView.vue  # 联邦智能体工作台
│   │   │   ├── SettingsView.vue          # 设置页面
│   │   │   └── ...
│   │   ├── components/
│   │   │   ├── agent/                 # Agent 专用组件
│   │   │   │   ├── LawyerSkillPanel.vue     # 律师技能面板（蓝色主题）
│   │   │   │   ├── TeacherSkillPanel.vue    # 教师技能面板（翠绿主题）
│   │   │   │   ├── ProgrammerSkillPanel.vue # 程序员技能面板（紫蓝主题）
│   │   │   │   ├── WriterSkillPanel.vue     # 作家技能面板（琥珀主题）
│   │   │   │   └── TraceTimeline.vue        # ReAct 执行轨迹
│   │   │   ├── agentos/               # AgentOS 控制台组件
│   │   │   │   ├── ContractEvidencePanel.vue   # 合同证据面板
│   │   │   │   ├── ContractRiskPanel.vue       # 合同风险面板
│   │   │   │   ├── ContractReportPreview.vue   # 审查报告预览
│   │   │   │   └── HumanReviewPanel.vue        # 人工审核面板
│   │   │   └── ...
│   │   ├── stores/                    # Pinia 状态管理
│   │   ├── services/api/              # API 服务层
│   │   ├── utils/agentos/             # AgentOS 工具（合同审查 artifact 提取等）
│   │   ├── router/                    # 路由配置
│   │   ├── i18n/                      # 国际化
│   │   └── themes/                    # 主题预设
│   ├── Dockerfile.dev
│   └── vite.config.ts
│
├── backend/                           # 后端项目 (Spring Boot + Java 17)
│   ├── src/main/java/com/kinlin/ai/
│   │   ├── controller/                # REST 控制器
│   │   │   ├── AgentOsGatewayController.java  # AgentOS 统一网关
│   │   │   ├── ChatController.java           # 对话控制器
│   │   │   ├── AuthController.java           # 认证控制器
│   │   │   └── ...
│   │   ├── service/                   # 业务服务层
│   │   │   ├── AgentOsGatewayService.java    # AgentOS 网关服务
│   │   │   ├── ChatService.java              # 对话服务
│   │   │   └── ...
│   │   ├── security/                  # 安全上下文
│   │   │   └── AuthenticatedUser.java        # 认证用户上下文
│   │   ├── entity/                    # JPA 实体
│   │   ├── repository/               # 数据访问层
│   │   ├── dto/                       # 数据传输对象
│   │   ├── config/                    # 配置类
│   │   └── filter/                    # 过滤器
│   ├── Dockerfile.dev
│   └── pom.xml
│
├── agent/                             # AI 服务 (FastAPI + LangGraph + RAG)
│   ├── app/
│   │   ├── main.py                    # FastAPI 应用入口
│   │   ├── config.py                  # 配置管理
│   │   ├── api/                       # API 路由
│   │   │   ├── agentos_core.py        # AgentOS 核心 API
│   │   │   ├── chat.py                # 对话 API
│   │   │   ├── rag.py                 # RAG 检索 API
│   │   │   └── ...
│   │   ├── llm/                       # LLM 网关
│   │   │   ├── gateway.py             # 统一 LLM 路由
│   │   │   ├── config.py              # LLM 配置
│   │   │   ├── schemas.py             # LLM 数据结构
│   │   │   ├── providers/             # LLM Provider 实现
│   │   │   └── prompts/               # Prompt 模板
│   │   ├── rag/                       # RAG 检索增强
│   │   │   ├── legal_retriever.py     # 法律知识检索器
│   │   │   ├── legal_document_loader.py  # 法律文档加载器
│   │   │   ├── legal_evidence_schema.py  # 证据数据结构
│   │   │   └── providers/             # 检索 Provider
│   │   ├── graphs/                    # LangGraph 状态图
│   │   │   └── legal_contract_review_stategraph.py  # 合同审查状态图
│   │   ├── ai_engine/                 # AI 引擎适配器
│   │   └── data/                      # 数据文件（知识库、数字人素材等）
│   ├── agentos.py                     # AgentOS 入口
│   ├── packs/                         # 行业能力包
│   │   ├── legal/                     # 律师 Pack（Agent + Skills + Workflows + Data）
│   │   ├── education/                 # 教师 Pack
│   │   ├── programmer/                # 程序员 Pack
│   │   └── writer/                    # 作家 Pack
│   ├── knowledge/                     # 知识库数据
│   │   └── legal/                     # 法律知识（法条、模板等）
│   ├── tests/                         # 测试
│   ├── requirements.txt
│   └── Dockerfile
│
├── agentOS/                           # AgentOS 核心框架 (自研)
│   ├── src/agentos/
│   │   ├── core/                      # 核心运行时
│   │   │   ├── runtime.py             # WorkflowRuntime
│   │   │   ├── workflow/              # 工作流编排、进度追踪、Task 管理
│   │   │   ├── governance/            # 治理（Checkpoint、Review、Trace）
│   │   │   └── models/types.py        # 核心类型定义
│   │   ├── domain/                    # 领域模型
│   │   │   ├── task.py                # Task 模型
│   │   │   ├── step.py                # Step 模型
│   │   │   ├── agent.py               # Agent 模型
│   │   │   └── workflow.py            # Workflow 模型
│   │   ├── agents/                    # Agent 基类与注册
│   │   ├── skills/                    # Skill 基类与注册
│   │   ├── packs/                     # Pack 注册与发现
│   │   ├── memory/                    # 会话记忆与 Workflow 上下文
│   │   ├── adapters/                  # 模型、检索、联邦适配器
│   │   ├── stores/                    # WorkflowStore 接口与实现
│   │   ├── communication/             # Agent 间通信
│   │   ├── infrastructure/            # 基础设施适配器
│   │   ├── governance/                # 治理策略引擎
│   │   └── recovery/                  # 恢复与重试
│   └── tests/                         # AgentOS 框架测试
│
├── docker/                            # Docker 生产部署配置
│   └── nginx/
│
├── docs/                              # 设计文档与方案
│   ├── design/                        # 架构设计与技术方案
│   ├── superpowers/plans/             # 开发计划
│   └── open-source-reference-survey.md  # 开源参考调研
│
├── docker-compose.yml                 # 开发环境 Docker Compose
├── dev.sh                             # Linux/macOS 开发启动脚本
├── dev.ps1                            # Windows PowerShell 开发启动脚本
├── .env.example                       # 环境变量示例
└── README.md                          # 本文件
```

## AgentOS 架构详解

### 核心组件

```
AgentOS Core:
用户请求
  → WorkflowRuntime（工作流生命周期管理）
    → Orchestrator（步骤编排）
      → TaskManager（Task 创建、分发、状态管理）
        → Pack Agent（领域 Agent 执行）
          → Skill（原子能力调用）
  → Trace / Checkpoint / Review（治理三件套）
  → Progress（步骤级进度追踪）
```

### 领域模型

| 模型 | 说明 |
|------|------|
| **Task** | 工作流中的任务单元，包含状态、优先级、依赖关系 |
| **Step** | Task 内的执行步骤，支持顺序/并行/条件流转 |
| **Agent** | 领域智能体，绑定特定 Pack 的 Skills |
| **Workflow** | 工作流定义，描述步骤拓扑与流转规则 |

### 四种 Agent 角色

| Agent | 主题色 | 核心 Skills |
|-------|--------|-------------|
| 律师 | 蓝色 #2563eb | 案情理解、法条检索、判例检索、证据分析、文书生成、合同审查、风险评估 |
| 教师 | 翠绿 #059669 | 学生诊断、教案生成、作业批改、错因推送、辅导答疑、学习路径规划 |
| 程序员 | 紫蓝 #7c3aed | 需求分析、代码生成、代码库语义搜索、图表生成 |
| 作家 | 琥珀 #d97706 | 大纲生成、风格分析、情节逻辑、润色对比、灵感扩展 |

### LLM 网关

LLM Gateway 提供统一的 AI 引擎访问层，支持：

- **Provider 抽象**: OpenAI-compatible 接口，支持 DeepSeek / Qwen / Mock（测试用）
- **自动路由**: 根据任务类型（文本/图像/语音）自动选择引擎
- **配置集中管理**: 模型名、温度、max_tokens 等统一在 LLM Config 中管理

### 合同审查 LangGraph 状态图

律师合同审查功能已迁移至 LangGraph 状态图架构：

- **状态节点**: 合同解析 → 法条匹配 → 风险评估 → 证据关联 → 报告生成
- **前端工作台**: 证据面板 + 风险面板 + 审查报告预览 + 人工审核
- **Artifact 提取**: 自动从工作流输出中提取结构化审查结果

## 快速开始

### 环境要求

- Docker Desktop / Docker Engine with Docker Compose
- （可选）本地开发需 JDK 17、Node.js 18+、Python 3.9+

### 1. 配置 API 密钥

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入 API 密钥：

```env
# DeepSeek API 密钥（文本生成主引擎）
DEEPSEEK_API_KEY=sk-your_deepseek_key

# 通义千问 API 密钥（图像/语音/多模态 + 文本回退）
DASHSCOPE_API_KEY=sk-your_qwen_key
```

### 2. 开发模式启动（推荐）

```bash
# Linux / macOS
./dev.sh up

# Windows PowerShell
./dev.ps1 up
```

这会启动全部服务：PostgreSQL、Redis、AI Service、Backend、Frontend。

开发模式端口：
- 前端: http://localhost:3000
- 后端: http://localhost:8080
- AI 服务: http://localhost:8000
- 后端远程调试: localhost:5005

常用命令：

```bash
./dev.sh logs     # 查看日志
./dev.sh restart  # 重启全部服务
./dev.sh build    # 重新构建镜像
./dev.sh down     # 停止服务
./dev.sh clean    # 停止并清理数据卷
```

### 3. 生产部署

```bash
docker compose -f docker/docker-compose.prod.yml up -d --build
```

### 4. 验证服务

```bash
# 检查后端健康
curl http://localhost:8080/health

# 检查 AI 服务健康
curl http://localhost:8000/health
```

## AgentOS API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/ai/core/tasks` | POST | 创建 AgentOS 任务 |
| `/ai/core/tasks` | GET | 查询任务列表 |
| `/ai/core/workflows/runs` | POST | 启动工作流 |
| `/ai/core/workflows/runs` | GET | 查询工作流列表 |
| `/ai/core/workflows/start` | POST | 直接创建并启动工作流 |
| `/ai/core/workflows/metrics` | GET | 查询治理指标 |
| `/ai/core/workflows/runs/{runId}` | GET | 查询工作流状态 |
| `/ai/core/workflows/runs/{runId}/progress` | GET | 查询步骤级进度 |
| `/ai/core/workflows/runs/{runId}/checkpoints` | GET | 查询恢复点 |
| `/ai/core/workflows/runs/{runId}/trace` | GET | 导出 Trace（JSON/Markdown） |
| `/ai/core/workflows/runs/{runId}/reviews` | GET/POST | 查询/提交人工审核 |
| `/ai/core/workflows/runs/{runId}/resume` | POST | 从 Checkpoint 恢复 |
| `/ai/chat/text/stream` | POST | 流式文本对话 (SSE) |
| `/ai/rag/query` | POST | RAG 检索 |

Java 网关提供 `/api/agentos/*` 入口，转发到 Python AgentOS `/ai/*`。

## 开发指南

### 新增行业 Pack

1. 在 `agent/packs/{pack_id}/` 创建目录结构：`agents/`、`skills/`、`workflows/`、`prompts/`、`data/`、`manifest.yaml`
2. 实现 `BaseAgent` 子类，绑定 Skills
3. 在 `manifest.yaml` 中声明 Pack 元数据
4. 在 `__init__.py` 中提供 `register_pack()` 注册入口

### 新增 Skill

1. 继承 `agentOS/src/agentos/skills/base.py` 中的 Skill 基类
2. 实现 `execute()` 方法
3. 在 Pack 的 `skills/__init__.py` 中注册
4. 为关键降级逻辑补充测试

### 新增 LLM Provider

1. 在 `agent/app/llm/providers/` 中实现 Provider 接口
2. 在 LLM Gateway 中注册新 Provider
3. 在 LLM Config 中添加对应配置项

### 代码规范

- 前端: TypeScript 严格模式，Vue 3 Composition API
- 后端: Java 17，Spring Boot 标准分层架构
- AI 服务: Python 3.9+，FastAPI 异步模式
- AgentOS: Python 3.9+，类型标注，领域驱动设计
- 所有配置通过环境变量 / `.env` 文件管理，不硬编码

## 常见问题

### 前端启动报错
- 确保 Node.js 版本 >= 18
- 删除 `node_modules` 后重新 `npm install`
- 清除浏览器缓存

### 后端连接数据库失败
- 确认 PostgreSQL 已启动：`docker ps | grep postgres`
- 检查 `application.yml` 中的数据库配置

### AI 服务启动警告
- `KYLIN_AI_API_KEY` 未设置：正常，系统会使用通义千问
- ChromaDB 初始化失败：确保 `agent/app/data/` 目录可写

### Agent 响应超时
- 检查 `agent.timeout-ms` 配置（默认 120 秒）
- 确认 AI 服务正常运行：`curl http://localhost:8000/health`
- 查看 AI 服务日志排查 Skill 执行错误

### Docker 部署问题
- 确保 Docker Desktop 已启动
- 端口冲突：检查 3000/8080/8000/5432/6379 端口是否被占用
- 使用 `docker compose logs <service>` 查看服务日志

## 许可证

MIT License
