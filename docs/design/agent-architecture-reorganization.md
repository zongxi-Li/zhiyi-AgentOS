# Agent 架构当前检查与后续调整

日期：2026-05-14

状态：用户已手动完成目录重整。后续以 `agent/agentos/` 为唯一 AgentOS canonical 路径，不再回退到旧核心包名或中间态应用内核心目录。

---

## 1. 当前结论

当前实现已经形成清晰的双层结构：

```text
agent/app/
  FastAPI 应用、API Route、配置、服务、数据入口

agent/agentos/
  AgentOS Runtime、Pack、Skill、ReAct、Memory、Store、Adapter
```

这套结构比之前更合理：`app` 负责对外服务，`agentos` 负责 Agent 能力底座。核心判断是：凡是与 Agent 生命周期、Workflow、Pack、Skill、Memory、Adapter 有关的代码，都应收敛到 `agent/agentos/`；凡是 HTTP 协议、FastAPI 路由、应用启动、传统业务服务，则继续放在 `agent/app/`。

---

## 2. 当前已成立的 Module 分工

| Module | 当前路径 | 当前状态 |
|---|---|---|
| Workflow Runtime | `agent/agentos/core/workflow_runtime.py` | 已有任务创建、启动、审核、恢复、取消 |
| Orchestrator | `agent/agentos/core/orchestrator.py` | 已按 Workflow 步骤分发 Agent |
| State Machine | `agent/agentos/core/state_machine.py` | 已约束 Workflow 和 Step 状态迁移 |
| Trace / Checkpoint / Review | `agent/agentos/core/trace.py`、`checkpoint.py`、`review.py` | 已支撑执行轨迹、恢复点和人工审核 |
| Agent Interface | `agent/agentos/agents/base.py` | 已定义 `BaseAgent` 和运行上下文 |
| Agent Registry | `agent/agentos/agents/registry.py` | 已支持按 domain / agent / capability 解析 |
| Pack | `agent/agentos/packs/*` | 法律 Pack 已有 Agent、Workflow、Prompt、Data；教育、程序员、作家目录已预留 |
| Skill | `agent/agentos/skills/base.py`、`agent/agentos/skills/builtin/*` | 保留可复用原子能力，由 Pack Agent 调用 |
| Legacy Chat Chain | 已删除 | 不再保留 ReAct 兼容链路和旧专业体聊天入口 |
| Store | `agent/agentos/stores/*` | 已有内存实现，数据库持久化待补 |
| Adapter | `agent/agentos/adapters/*` | 模型、检索、联邦能力已集中到适配层 |

---

## 3. 现在应该怎么做

### P0：先稳住当前结构

- 所有 Python 导入统一使用 `agentos.*`。
- 文档、README、测试只把 `agent/agentos/` 作为 AgentOS 路径。
- `agent/app/api/*` 可以引用 `agentos`，但 `agentos/core` 不反向依赖 `app`。
- 不再新增应用内核心目录、旧核心包名目录或顶层核心目录。

### P1：把所有专业能力收拢进统一 Workflow 生命周期

旧的 `/ai/agent/{role}/chat` 专业体入口已经删除。接下来不再维护两套调用协议，而是直接把四类行业 Pack 的能力整理进 `WorkflowRuntime`、`WorkflowRegistry` 和 `BaseAgent`。

当前统一链路是：

```text
POST /ai/core/tasks
  -> WorkflowRuntime.create_task()
  -> WorkflowRuntime.start()
  -> AgentRegistry.resolve()
  -> Pack Agent.run()
  -> Trace / Checkpoint / Review
```

这样前端和 Java 后端只需要围绕 `/ai/core/*` 扩展，不再回到旧聊天入口。

### P1：让 Store 成为真实持久化 Seam

现在的 `MemoryWorkflowStore` 适合测试和 Demo，但不适合长期任务：

```text
agent/agentos/stores/workflow_store.py
agent/agentos/stores/memory_workflow_store.py
```

建议下一步新增数据库实现，例如：

```text
agent/agentos/stores/sqlite_workflow_store.py
```

接口保持不变，`WorkflowRuntime` 只依赖 `WorkflowStore`，不要直接写数据库细节。

### P1：Pack 注册从代码驱动走向 manifest 驱动

当前法律 Pack 通过 `register_pack()` 注册 Agent 和 Workflow。短期可以保留，后续建议让 `manifest.yaml` 声明更多信息：

```yaml
id: legal
name: Legal Demo Pack
version: 0.1.0
workflows:
  - workflows/contract_review.yaml
agents:
  - agentos.packs.legal.agents.case_intake:CaseIntakeAgent
```

这样新增 Pack 时，默认运行时可以按 manifest 自动加载，减少硬编码。

### P2：补齐四类专业 Pack

当前 `education`、`programmer`、`writer` 已有目录和内置 Skill，但 Core Workflow 还主要验证法律 Pack。后续建议按这个顺序推进：

1. 为每个 Pack 写一个最小 Workflow。
2. 为每个 Pack 补 2-3 个关键 Agent。
3. 复用已有 `skills/builtin` 能力。
4. 写 Pack 注册测试和 Workflow 冒烟测试。

---

## 4. 保留与删除判断

### 应保留

- `agent/agentos/skills/builtin/*`：四类专业体已有 Skill 应继续复用。
- `agent/agentos/adapters/*`：外部能力统一入口。

### 应避免新增

- 应用内核心目录
- 旧核心包名目录
- 顶层核心目录
- 让 `core/` 直接 import 某个行业 Pack 的业务实现
- 在 API Route 里继续堆复杂执行流程

### 已清理

- 旧专业体路由模块
- 旧 ReAct 兼容链路
- 旧会话记忆入口
- 旧技能注册表

### 可后续清理

- 没有被测试、API 或 Pack 引用的旧路径文档。
- 重复的专业体结果聚合逻辑。
- Route Module 中直接实例化模型、联邦、检索能力的代码。

---

## 5. 实现检查清单

- [ ] 搜索旧大小写包名、旧核心包名和中间态路径，不再出现活动路径漂移。
- [ ] `python -m pytest tests/test_agentos_core.py -q` 通过。
- [ ] `python -m pytest tests/test_programmer_skills.py tests/test_teacher_skills.py tests/test_writer_skills.py -q` 通过。
- [ ] `python -m compileall app agentos tests` 通过。
- [ ] 新增 Pack 时只需要改 Pack 目录、注册入口和测试。
- [ ] Core 测试能覆盖启动、审核、失败恢复、取消和最终输出。

---

## 6. 当前推荐路线

短期不要再做大规模目录移动。现在更重要的是把运行模型收拢：

```text
先稳定 agent/agentos 包名
再让文档与测试承认当前结构
再把旧聊天入口接到 WorkflowRuntime
最后补持久化 Store 和 manifest 驱动 Pack 加载
```

这条路线的目标是让架构从“目录已经整理好”继续走向“运行时也真正统一”。
