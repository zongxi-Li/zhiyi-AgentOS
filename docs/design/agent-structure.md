# 知弈 AgentOS 当前结构

日期：2026-05-14

本文以当前实现为准。`agent/agentos/` 是 Agent 运行时、Pack、Skill、ReAct 和 Adapter 的 canonical 包路径；`agent/app/` 只保留 FastAPI 入口、API Route、配置、服务和数据入口。

---

## 1. 顶层结构

```text
agent/
  app/
    main.py
    config.py
    paths.py
    api/
      agentos_core.py
      agent_lawyer.py
      agent_teacher.py
      agent_programmer.py
      agent_writer.py
      chat.py
      rag.py
      ...
    ai_engine/
    services/
    middleware/
    data/

  agentos/
    __init__.py
    core/
    agents/
    packs/
    skills/
    react/
    memory/
    stores/
    adapters/

  tests/
```

---

## 2. AgentOS 包结构

```text
agent/agentos/
  core/
    types.py
    orchestrator.py
    state_machine.py
    workflow_registry.py
    workflow_runtime.py
    trace.py
    checkpoint.py
    review.py
    evaluation.py

  agents/
    base.py
    registry.py

  packs/
    legal/
      manifest.yaml
      workflows/
      agents/
      skills/
      prompts/
      data/
    education/
    programmer/
    writer/

  skills/
    base.py
    registry.py
    builtin/

  react/
    planner.py
    executor.py
    tool_router.py

  memory/
    session_memory.py
    workflow_memory.py

  stores/
    workflow_store.py
    memory_workflow_store.py

  adapters/
    model_adapter.py
    retrieval_adapter.py
    federated_adapter.py
    retrieval/
```

---

## 3. 模块职责

| 模块 | 职责 | 约束 |
|---|---|---|
| `core` | 管理 `AgentTask`、`WorkflowRun`、状态机、Trace、Checkpoint、审核和评估 | 不写行业逻辑，不直接依赖具体 Pack |
| `agents` | 定义 `BaseAgent`、`AgentRunContext`、`AgentRegistry` | 只提供统一 Agent 接口和发现机制 |
| `packs` | 承载行业能力包：Workflow、Agent、Prompt、数据、规则 | 行业能力从 Pack 注册进入系统 |
| `skills` | 定义 Skill 接口、内置 Skill 注册表 | Skill 是可复用原子能力，可被 ReAct 或 Pack Agent 调用 |
| `react` | 兼容现有专业体聊天链路的局部规划、执行和工具路由 | 作为步骤内部能力，不再承担全局 Workflow 生命周期 |
| `memory` | 会话记忆和 Workflow 中间上下文 | 与持久化 Store 分离 |
| `stores` | Workflow 任务和运行记录的存储接口与内存实现 | 后续数据库持久化从这里接入 |
| `adapters` | 模型、检索、联邦增强等外部能力适配 | 调用外部系统集中从 Adapter 进入 |

---

## 4. 当前运行链路

### 4.1 AgentOS Core Workflow 链路

```text
POST /ai/core/tasks
  -> WorkflowRuntime.create_task()
  -> WorkflowRegistry.recommend()

POST /ai/core/workflows/runs
  -> WorkflowRuntime.start()
  -> Orchestrator.select_next_step()
  -> AgentRegistry.resolve()
  -> Pack Agent.run()
  -> TraceStore / CheckpointStore / ReviewManager
```

入口文件：`agent/app/api/agentos_core.py`

默认运行时：`agent/agentos/core/workflow_runtime.py`

当前已接入的演示 Pack：`agent/agentos/packs/legal/`

### 4.2 兼容专业体聊天链路

```text
POST /ai/agent/{lawyer,teacher,programmer,writer}/chat
  -> agent/app/api/agent_*.py
  -> ReactPlanner
  -> ReactExecutor
  -> ToolRouter
  -> SkillRegistry
  -> Builtin Skill
  -> Model / Retrieval / Federated Adapter
```

这条链路继续对前端和 Java 后端提供兼容接口。它使用 `agentos.react`、`agentos.skills`、`agentos.memory` 和 `agentos.adapters`，但暂时还没有完全纳入 `WorkflowRun` 生命周期。

---

## 5. 设计原则

```text
Core 管生命周期。
Pack 管行业能力。
Workflow 用配置定义步骤。
Agent 执行专业步骤。
Skill 提供原子能力。
Adapter 连接外部模型、检索、联邦和存储。
API Route 只做协议适配，不承载复杂执行逻辑。
```

---

## 6. 新增 Pack 的方式

1. 在 `agent/agentos/packs/{pack_id}/` 下创建 `manifest.yaml`。
2. 在 `workflows/` 中放置 Workflow YAML，声明步骤、Agent、审核节点和流转关系。
3. 在 `agents/` 中实现 `BaseAgent` 子类。
4. 如果 Pack 有专属工具，放入 Pack 内的 `skills/`；可复用工具放入 `agent/agentos/skills/builtin/`。
5. 在 Pack 的 `__init__.py` 中提供 `register_pack(agent_registry, workflow_registry)`。
6. 在默认运行时或启动配置中注册 Pack。
7. 为 Workflow、Agent 注册和关键执行路径补充测试。

---

## 7. 当前应继续推进的工作

| 优先级 | 工作 | 目标 |
|---|---|---|
| P0 | 保持所有 Python 导入统一为 `agentos.*` | 避免大小写包名和旧路径漂移 |
| P0 | 文档统一以 `agent/agentos` 为 canonical | 后续检查实现时不再混用旧目录 |
| P1 | 把旧专业体聊天入口逐步包成 Workflow 兼容 Adapter | 让 Trace、Checkpoint、Review 进入同一生命周期 |
| P1 | 为 `WorkflowStore` 增加数据库实现 | 解决进程重启后任务状态丢失 |
| P1 | 让 Pack manifest 驱动注册 | 减少默认运行时里的硬编码注册 |
| P2 | 教育、程序员、作家 Pack 补齐 Workflow 和 Pack Agent | 让四类专业体都能走 AgentOS Core |
| P2 | 前端工作台接入 `/ai/core/*` | 展示真实 `WorkflowRun`、Trace、Checkpoint 和审核状态 |

---

## 8. 判断标准

后续调整以这几条作为检查线：

- 业务能力是否通过 `packs/` 进入，而不是写进 `core/`。
- 全局任务生命周期是否由 `WorkflowRuntime` 管理。
- `core/` 是否仍然不知道法律、教育、程序员、作家等行业细节。
- API Route 是否足够薄，只负责请求/响应和兼容协议。
- 新增一个 Pack 是否主要改 Pack 目录，而不是同时改多个无关模块。
