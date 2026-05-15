# 知弈 AI Service

Python AI 服务，提供 FastAPI 接口、模型调用、RAG、专业 Agent 和 AgentOS Workflow Runtime。

## 当前结构

```text
agent/
  app/
    main.py
    config.py
    api/
    services/
    ai_engine/
    middleware/
    data/

  agentos/
    core/
    agents/
    packs/
    skills/
    memory/
    stores/
    adapters/

  tests/
```

`app/` 负责应用启动、HTTP 路由、配置和传统服务；`agentos/` 是 Agent 运行时核心，负责 Workflow、Pack、Skill、Memory、Store 和 Adapter。

## AgentOS 入口

- `POST /ai/core/tasks`：创建任务并推荐 Workflow。
- `POST /ai/core/workflows/runs`：启动 WorkflowRun。
- `POST /ai/core/workflows/start`：Workbench 直接创建任务并启动 WorkflowRun。
- `GET /ai/core/workflows/runs/{runId}`：查询运行状态。
- `POST /ai/core/workflows/runs/{runId}/reviews`：提交人工审核结果。
- `POST /ai/core/workflows/runs/{runId}/resume`：从 Checkpoint 恢复。
- `POST /ai/chat/workflows/upgrade`：将 Chat 输入和上下文升级为 WorkflowRun。

旧的 `/ai/agent/{role}/chat` 专业体入口已移除，统一以 `/ai/core/*` 的 `WorkflowRun` 生命周期为准。

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置

`.env` 文件放在项目主目录，即与 `agent/`、`backend/`、`frontend/` 同级。

```text
Kinlin_AI/
  .env
  agent/
  backend/
  frontend/
```

常用配置：

```env
DASHSCOPE_API_KEY=sk-your_api_key_here
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL_FAST=qwen-turbo
QWEN_MODEL_BALANCED=qwen-plus
QWEN_MODEL_ADVANCED=qwen-max
QWEN_MODEL_LATEST=qwen3-max
QWEN_ENABLED=true

DEEPSEEK_API_KEY=sk-your_deepseek_key
DEEPSEEK_MODEL=deepseek-chat
```

系统全局使用 `app/config.py` 中的 `settings` 作为配置来源。

## 启动服务

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

或：

```bash
python app/main.py
```

## 测试

在 `agent/` 目录下运行：

```bash
python -m pytest tests/test_agentos_core.py -q
python -m pytest tests/test_programmer_skills.py tests/test_teacher_skills.py tests/test_writer_skills.py -q
python -m compileall app agentos tests
```

## 新增 Pack

1. 在 `agentos/packs/{pack_id}/` 创建 `manifest.yaml`、`workflows/`、`agents/`、`prompts/`、`data/`。
2. 实现 `BaseAgent` 子类。
3. 在 Workflow YAML 中声明步骤、Agent、审核节点和流转关系。
4. 在 Pack 的 `__init__.py` 中提供 `register_pack(agent_registry, workflow_registry)`。
5. 为 Pack 注册和 Workflow 冒烟路径添加测试。
