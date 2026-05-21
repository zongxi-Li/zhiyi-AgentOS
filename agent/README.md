# 知弈 AI Service

`agent/` 是 Python 应用服务层，负责 FastAPI 入口、协议适配、传统 AI 服务、数据目录和领域 Pack 承载。AgentOS Core 已迁移到仓库根目录的 `agentOS/src/agentos/`。

## 当前结构

```text
agent/
  app/                    # FastAPI 应用层
    main.py
    config.py
    paths.py
    api/
    services/
    ai_engine/
    middleware/
    data/

  packs/                  # 领域能力包，由应用层选择加载
    legal/
    education/
    programmer/
    writer/

  tests/
  agentos.py              # 兼容入口，转发到 ../agentOS/src/agentos
```

```text
../agentOS/src/agentos/   # AgentOS Core
  core/
  agents/
  packs/
  skills/
  memory/
  stores/
  adapters/
```

`app/` 负责 HTTP 路由、配置、传统服务和兼容协议；`packs/` 承载法律、教育、程序员、作家等领域能力；`agentOS/src/agentos/` 负责 Workflow Runtime、Agent/Skill Interface、Pack Registry、Memory、Store 和 Adapter。

## AgentOS 入口

- `POST /ai/core/tasks`：创建任务并推荐 Workflow。
- `POST /ai/core/workflows/runs`：启动 WorkflowRun。
- `POST /ai/core/workflows/start`：Workbench 直接创建任务并启动 WorkflowRun。
- `GET /ai/core/workflows/metrics`：查询 WorkflowRun 治理指标。
- `GET /ai/core/workflows/runs/{runId}`：查询运行状态。
- `GET /ai/core/workflows/runs/{runId}/checkpoints`：查询恢复点列表。
- `GET /ai/core/workflows/runs/{runId}/trace`：导出 Trace，可选 `format=json` 或 `format=markdown`。
- `GET /ai/core/workflows/runs/{runId}/reviews`：查询审核记录。
- `POST /ai/core/workflows/runs/{runId}/reviews`：提交人工审核结果。
- `POST /ai/core/workflows/runs/{runId}/resume`：从 Checkpoint 恢复。
- `POST /ai/chat/workflows/upgrade`：将 Chat 输入和上下文升级为 WorkflowRun。

## 配置

`.env` 文件放在项目主目录，即与 `agent/`、`agentOS/`、`backend/`、`frontend/` 同级。

```text
Kinlin_AI/
  .env
  agent/
  agentOS/
  backend/
  frontend/
```

Pack 默认从 `agent/packs/` 自动发现；如需覆盖，可设置：

```env
AGENTOS_PACKS_DIR=E:/Project/Kinlin_AI/agent/packs
AGENTOS_DATA_DIR=E:/Project/Kinlin_AI/agent/app/data
AGENTOS_WORKFLOW_DB_PATH=E:/Project/Kinlin_AI/agent/agentos-workflow.db
```

## 启动服务

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 测试

在项目根目录运行：

```bash
python -m pytest agent/tests/test_architecture_migration.py -q
python -m pytest agent/tests/test_pack_registry.py agent/tests/test_agentos_core.py -q
python -m pytest agent/tests/test_programmer_skills.py agent/tests/test_teacher_skills.py agent/tests/test_writer_skills.py -q
```

## 新增 Pack

1. 在 `agent/packs/{pack_id}/` 创建 `manifest.yaml`、`workflows/`、`agents/`、`skills/`、`prompts/`、`data/`。
2. 实现 `agentos.agents.BaseAgent` 子类。
3. 在 Workflow YAML 中声明步骤、Agent、审核节点和流转关系。
4. 在 Pack 的 `__init__.py` 中提供 `register_pack(agent_registry, workflow_registry)`。
5. 默认运行时会通过 `agentos.packs.registry` 自动发现并加载已启用 Pack。
6. 为 Pack 注册和 Workflow 冒烟路径添加测试。
