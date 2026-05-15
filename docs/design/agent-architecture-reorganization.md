# Agent 架构重整梳理文档

日期：2026-05-14

范围：`frontend/`、`backend/`、`agent/` 中与 Agent、Workflow、Skill、联邦增强、控制台展示相关的实现。

结论：当前 Agent 架构最大的问题不是缺少功能，而是同时存在两套运行模型。旧专业体链路已经能对外工作，新 AgentOS Core 也有运行时雏形和测试，但两者没有收拢到同一个任务生命周期、同一套 Trace、同一套 Pack 注册机制。建议以 `WorkflowRuntime` 作为唯一任务运行 Module，旧 ReAct 专业体逐步下沉为兼容 Adapter 和 Pack 内部执行能力。

---

## 1. 本文术语

为避免继续混用概念，后续统一使用这些词：

- **Module**：有接口和实现的代码单元，可以是 Python 包、类、函数、Java 类或前端状态切片。
- **Interface**：调用方必须知道的一切，包括字段、状态、错误模式、调用顺序和配置。
- **Implementation**：Interface 背后的具体代码。
- **Seam**：可以替换行为的位置，例如从内存存储换成数据库存储的位置。
- **Adapter**：位于 Seam 上的具体实现，例如 `InMemoryWorkflowStore` 或 `PythonAgentHttpAdapter`。
- **Leverage**：调用方通过小 Interface 获得的能力。
- **Locality**：修改、排错和测试集中在一个位置。

---

## 2. 当前实际架构

### 2.1 旧专业体链路，当前对外主链路

```text
Frontend agent*.ts / FederatedAgentWorkbenchView
  -> Java AgentController
  -> Java AgentGatewayService
  -> Python /ai/agent/{lawyer,teacher,programmer,writer}/chat
  -> agent_*.py
  -> ReactPlanner
  -> ReactExecutor
  -> ToolRouter
  -> BaseSkill 实现
  -> AIService / FederatedAdapter / session_memory_store
```

相关文件：

- `frontend/src/services/api/agentLawyer.ts`
- `frontend/src/services/api/agentTeacher.ts`
- `frontend/src/services/api/agentProgrammer.ts`
- `frontend/src/services/api/agentWriter.ts`
- `frontend/src/views/FederatedAgentWorkbenchView.vue`
- `backend/src/main/java/com/kinlin/ai/controller/AgentController.java`
- `backend/src/main/java/com/kinlin/ai/service/AgentGatewayService.java`
- `agent/app/api/agent_lawyer.py`
- `agent/app/api/agent_teacher.py`
- `agent/app/api/agent_programmer.py`
- `agent/app/api/agent_writer.py`
- `agent/app/core/react/planner.py`
- `agent/app/core/react/executor.py`
- `agent/app/core/react/tool_router.py`
- `agent/app/core/skills/**`

这条链路的优点是已经可用，教师、律师、程序员、作家都有技能和前端展示。缺点是角色、技能、答案合成、联邦增强、记忆写入散落在多个 Route Module 中；新增一个专业体需要同时改 Python、Java、前端和 DTO。

### 2.2 新 AgentOS Core 链路，当前是雏形链路

```text
Python /ai/core/tasks
  -> WorkflowRuntime.create_task()
  -> WorkflowRegistry.recommend()

Python /ai/core/workflows/runs
  -> WorkflowRuntime.start()
  -> Orchestrator.select_next_step()
  -> AgentRegistry.resolve()
  -> Pack Agent.run()
  -> TraceStore / CheckpointStore / ReviewManager
```

相关文件：

- `agent/app/api/agentos_core.py`
- `agent/app/core/orchestration/types.py`
- `agent/app/core/orchestration/workflow_runtime.py`
- `agent/app/core/orchestration/orchestrator.py`
- `agent/app/core/orchestration/workflow_registry.py`
- `agent/app/core/orchestration/state_machine.py`
- `agent/app/core/orchestration/trace.py`
- `agent/app/core/orchestration/checkpoint.py`
- `agent/app/core/orchestration/review.py`
- `agent/app/core/agents/base.py`
- `agent/app/core/agents/registry.py`
- `agent/app/core/agents/packs/legal/**`
- `agent/tests/test_agentos_core.py`

这条链路的优点是已经有 `AgentTask`、`WorkflowDefinition`、`WorkflowRun`、`WorkflowStep`、`TraceEvent`、`Checkpoint`、`ReviewDecision` 等核心语言，也有测试覆盖。缺点是目前只在 Python 内部可用，Java 和前端没有接入；运行状态、Trace、Checkpoint 都是内存实现；法律 Pack 的 Agent 没有复用现有法律 Skill，而是写了另一套轻量实现。

### 2.3 文档与实现漂移

当前文档里多处仍写 `agent/app/agent_core`，而实现已经迁移到 `agent/app/core`。`docs/design/core-arch.md` 和 `docs/design/core-todo.md` 描述的是目标态，`README.md` 仍偏向旧 ReAct 专业体架构。建议把 `agent/app/core` 作为唯一命名，不再回到 `agent_core`。

---

## 3. 主要混乱点

1. **两套运行生命周期并存**

旧链路以 `sessionId + skillsUsed + AgentTraceStep` 为中心；新链路以 `taskId + runId + WorkflowStep + TraceEvent + Checkpoint` 为中心。两者状态模型、Trace 结构和恢复能力不兼容。

2. **API Route Module 承担了太多实现**

`agent_lawyer.py`、`agent_teacher.py`、`agent_programmer.py`、`agent_writer.py` 同时负责接参、读取记忆、规划、执行、结果抽取、LLM 合成、简体中文校验、写入记忆和错误降级。它们不是薄 Adapter，而是把运行逻辑复制了四份。

3. **角色和技能注册是硬编码的**

`ReactPlanner` 按 role 写死规划逻辑，`ToolRouter` 按 role 写死技能表，Java `AgentGatewayService` 写死四个 URL，前端写死四个 `agent*.ts`。新增一个 Pack 没有单一入口。

4. **Pack 的位置和职责不清**

当前路径是 `agent/app/core/agents/packs/legal`，但 Pack 不只包含 Agent，还应该包含 Workflow、Skill、Prompt、知识和规则。把 Pack 放在 `agents` 下面会让后续教育、金融、政务等 Pack 的归属越来越别扭。

5. **状态、Trace 和 Checkpoint 没有持久化 Seam**

`WorkflowRuntime.tasks`、`WorkflowRuntime.runs`、`TraceStore`、`CheckpointStore` 都在内存里。进程重启后运行状态丢失，Java 只持久化聊天交换，不持久化 WorkflowRun。

6. **联邦增强和模型调用散落在技能、Route Module 和服务里**

`FederatedAdapter()`、`AIService()` 在多个文件内直接实例化。测试和替换模型供应商时缺少统一 Seam。

7. **前端工作台仍是演示优先**

`FederatedAgentWorkbenchView.vue` 的 API 模式调用旧律师 Agent，并把 ReAct trace 映射成流程步骤。它没有直接接入 `WorkflowRun`、`Checkpoint`、`ReviewDecision`，所以展示语言比真实运行时更先进。

8. **Trace 命名有风险**

旧 `AgentTraceStep` 里有 `thought` 字段，前端也有“思维链视图”。这里目前是规划说明，不是模型内部推理链。建议产品文案统一改成“执行轨迹”或“步骤说明”，避免误导。

---

## 4. 推荐目标架构

### 4.1 总原则

```text
Core 只管理任务运行。
Pack 提供行业能力。
Agent 执行专业步骤。
Skill 完成原子能力。
Adapter 连接模型、检索、联邦、存储和旧入口。
Java 和前端只面向稳定 Interface，不写死行业实现。
```

### 4.2 推荐主链路

```text
Frontend AgentOS Console
  -> Java AgentOS Gateway
  -> Python AgentOS Core API
  -> WorkflowRuntime
  -> Orchestrator
  -> AgentRegistry / WorkflowRegistry
  -> Pack Agent
  -> SkillRegistry
  -> Model / Retrieval / Federated Adapters
  -> WorkflowStore / TraceStore / CheckpointStore
```

### 4.3 旧专业体如何保留

旧 `/ai/agent/{role}/chat` 不应立即删除。建议变成兼容 Adapter：

```text
/ai/agent/lawyer/chat
  -> CompatAgentChatAdapter
  -> 创建一个单步或多步 WorkflowRun
  -> 复用 WorkflowRuntime
  -> 返回旧 AgentChatResponse 形状
```

这样旧前端和 Java 不会马上断，但所有执行过程会逐步进入同一套 `WorkflowRun`、`TraceEvent`、`Checkpoint`。

### 4.4 ReAct 模块的新位置

`ReactPlanner`、`ReactExecutor`、`ToolRouter` 不再作为系统级运行时，而是作为 Pack Agent 内部可选执行引擎：

```text
Pack Agent.run()
  -> 可直接实现专业逻辑
  -> 或委托 ReActStepEngine
       -> SkillRegistry
       -> Skill.run()
```

Core 只看到 `BaseAgent.run(context) -> AgentOutput`，不直接知道 ReAct、Prompt 或具体技能。

---

## 5. 建议目录形态

保留 `agent/app/core` 作为 canonical 路径，后续按职责收拢：

```text
agent/
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
```

说明：

- `orchestration/` 是 Core 的运行 Module。
- `agents/` 只保存 Agent Interface 和注册机制。
- `packs/` 才是行业扩展入口，避免把 Workflow、Skill、Prompt 塞进 `agents/`。
- `skills/registry.py` 用于替代 `ToolRouter` 内部硬编码技能表。
- `stores/` 建立持久化 Seam，第一版可以仍然是内存 Adapter。
- `adapters/` 建立模型、检索、联邦增强的替换 Seam。

---

## 6. Deepening Opportunities

### 6.1 统一任务生命周期 Module

**Files**

- `agent/app/api/agent_*.py`
- `agent/app/api/agentos_core.py`
- `agent/app/core/orchestration/workflow_runtime.py`
- `agent/app/core/react/**`

**Problem**

旧专业体链路和新 WorkflowRuntime 各自维护状态、Trace 和结果形状。删除其中任意一套，复杂度都会重新出现在调用方，说明当前 Module 没有形成足够深的 Interface。

**Solution**

把 `WorkflowRuntime` 定为唯一任务运行 Module。旧专业体 Route Module 变成兼容 Adapter，只做请求/响应转换，不再直接编排。

**Benefits**

Locality：状态、失败、恢复、审核逻辑集中在 `WorkflowRuntime`。

Leverage：Java、前端、测试都只学习一套 `WorkflowRun` Interface。

测试收益：端到端测试从“四个专业体各测一套”收敛为“工作流生命周期 + Pack 输出”两层测试。

### 6.2 建立 Pack 注册 Module

**Files**

- `agent/app/core/agents/packs/legal/**`
- `agent/app/core/agents/registry.py`
- `agent/app/core/orchestration/workflow_registry.py`
- `agent/app/core/react/tool_router.py`
- `agent/app/core/skills/**`

**Problem**

Pack 目前挂在 `agents/packs` 下面，技能表在 `ToolRouter` 中硬编码。法律 demo Pack 和旧律师 Skill 是两套实现。

**Solution**

把 Pack 提升为一等 Module：`core/packs/{packId}`。Pack 通过 `manifest.yaml` 注册 Workflow、Agent、Skill 和 Prompt。`SkillRegistry` 负责按 `skillName` 解析 Skill。

**Benefits**

Locality：教育 Pack、法律 Pack、写作 Pack 的业务知识集中在各自目录。

Leverage：新增行业时只新增 Pack，不需要改 Core、Java 网关和前端基础结构。

测试收益：可以对每个 Pack 做 manifest 校验、WorkflowDefinition 校验、Agent/Skill 契约测试。

### 6.3 建立 WorkflowStore Seam

**Files**

- `agent/app/core/orchestration/workflow_runtime.py`
- `agent/app/core/orchestration/trace.py`
- `agent/app/core/orchestration/checkpoint.py`
- `backend/src/main/java/com/kinlin/ai/service/AgentConversationPersistenceService.java`

**Problem**

当前 `tasks`、`runs`、`trace`、`checkpoints` 都在内存对象内。恢复和审计只能在单进程内成立。

**Solution**

新增 `WorkflowStore` Interface，先提供 `InMemoryWorkflowStore` Adapter，后续再接 PostgreSQL/Redis。`TraceStore` 和 `CheckpointStore` 不直接绑 `WorkflowRun` 对象，而是通过 Store 写入。

**Benefits**

Locality：持久化策略集中在 Store Adapter。

Leverage：恢复、审计、前端刷新、Java 落库都共享同一套数据源。

测试收益：Store 可以单测，Runtime 可以用内存 Adapter 做快速测试。

### 6.4 收敛 Java Agent 网关

**Files**

- `backend/src/main/java/com/kinlin/ai/controller/AgentController.java`
- `backend/src/main/java/com/kinlin/ai/service/AgentGatewayService.java`
- `backend/src/main/java/com/kinlin/ai/dto/agent/AgentChatResponse.java`
- `backend/src/main/resources/application.yml`

**Problem**

Java 目前写死 lawyer/teacher/programmer/writer 四个方法和四个 Python URL。`AgentChatResponse` 也塞入多个角色专属字段。

**Solution**

新增 `AgentOsGatewayService`，面向 Python `/ai/core/*`。旧 `AgentController` 保留，但内部转发到通用 Gateway 或兼容 Adapter。新增 `dto/agentos` 描述 `WorkflowRun`、`WorkflowStep`、`TraceEvent`、`Checkpoint`、`ReviewDecision`。

**Benefits**

Locality：Java 只负责鉴权、转发、审计和持久化摘要。

Leverage：新增 Pack 不需要新增 Java 方法。

测试收益：网关测试只验证通用 Workflow Interface。

### 6.5 让前端工作台接入真实 WorkflowRun

**Files**

- `frontend/src/views/FederatedAgentWorkbenchView.vue`
- `frontend/src/services/api/agent*.ts`
- `frontend/src/components/agent/TraceTimeline.vue`
- `frontend/src/router/index.ts`

**Problem**

工作台以演示数据为主，API 模式仍调用旧律师 Agent。它显示的是“任务流”，但真实数据来自 `AgentTraceStep`，不是 `WorkflowStep`。

**Solution**

新增 `frontend/src/services/api/agentos.ts` 和 `frontend/src/stores/workflow.ts`。工作台读取 `WorkflowRun.steps`、`trace`、`checkpoints`、`status`。旧 Agent 面板只负责渲染 Pack artifacts。

**Benefits**

Locality：状态管理集中在 workflow store。

Leverage：同一个控制台可展示法律、教育、写作、程序员 Pack。

测试收益：前端可以用固定 `WorkflowRun` fixture 测状态、审核、恢复 UI。

### 6.6 收拢模型、检索和联邦 Adapter

**Files**

- `agent/app/services/aiservice.py`
- `agent/app/core/federated/federated_adapter.py`
- `agent/app/core/retrieval/**`
- `agent/app/core/skills/**`
- `agent/app/api/agent_*.py`

**Problem**

`AIService()`、`FederatedAdapter()` 在多个 Module 里直接创建，技能测试和模型替换成本高。

**Solution**

建立 `RuntimeAdapters` 或 `AdapterRegistry`，由 bootstrap 注入模型、检索、联邦、存储 Adapter。Skill 和 Agent 从 context 中拿能力，不自行 new。

**Benefits**

Locality：供应商切换、超时、降级策略集中处理。

Leverage：所有 Pack 自动获得同样的模型和联邦策略。

测试收益：测试可以注入 fake adapter，不需要真实网络或模型密钥。

### 6.7 清理文档命名漂移

**Files**

- `README.md`
- `docs/design/core.md`
- `docs/design/core-arch.md`
- `docs/design/core-todo.md`
- `docs/design/agent-structure.md`

**Problem**

文档同时出现 `agent_core`、`core`、旧 ReAct 专业体和新 AgentOS Core 目标态。实现检查时会误判哪些已经完成。

**Solution**

把 `agent/app/core` 写成唯一真实路径。旧专业体标注为“兼容入口”，新 AgentOS Core 标注为“目标主入口”。`core-todo.md` 改为按迁移阶段追踪。

**Benefits**

Locality：架构决策不会散落在 README 和多个设计文档里。

Leverage：后来者能按文档找到真实代码。

测试收益：文档检查可以用 `rg agent_core` 作为漂移检查之一。

---

## 7. 分阶段调整路线

### Phase 0：确认方向，不动行为

- 确认 `agent/app/core` 是唯一核心路径。
- 确认 `WorkflowRuntime` 是唯一任务生命周期 Module。
- 确认旧 `/ai/agent/*/chat` 是兼容 Adapter，不再作为新功能主路径。
- 更新 README 和设计文档里的 `agent_core` 命名。

### Phase 1：把 Core 运行时变深

- 新增 `WorkflowStore` Interface 和 `InMemoryWorkflowStore` Adapter。
- 把 `WorkflowRuntime.tasks/runs` 包装进 Store。
- 统一 `TraceEvent` 写入路径。
- 保持 `agent/tests/test_agentos_core.py` 通过。

### Phase 2：把旧专业体接入 Core

- 新增 `CompatAgentChatAdapter`。
- 将 lawyer/teacher/programmer/writer 入口转换成单步或多步 WorkflowRun。
- 旧 Response 字段通过 Adapter 从 `WorkflowRun.output.artifacts` 中映射。
- 保留旧前端可用性。

### Phase 3：重塑 Pack

- 新建 `agent/app/core/packs/legal`，迁移法律 demo pack。
- 把现有法律 Skill 纳入 legal Pack 或明确标注为 builtin Skill。
- 为 teacher/programmer/writer 建立 Pack manifest。
- 新增 `SkillRegistry`，替换 `ToolRouter` 的硬编码技能表。

### Phase 4：Java 和前端接入 AgentOS Core

- 新增 Java `AgentOsGatewayService`、`AgentOsController`、`WorkflowController`。
- 新增前端 `agentos.ts`、`workflow.ts` store。
- `FederatedAgentWorkbenchView.vue` 改为真实 WorkflowRun 控制台。
- 增加审核、重跑、恢复、取消入口。

### Phase 5：持久化、治理和产品化

- Store Adapter 接 PostgreSQL/Redis。
- Java 持久化 WorkflowRun 摘要、审计记录和用户操作。
- Evaluation 暴露查询入口。
- Trace 文案统一为“执行轨迹”，避免“思维链”误导。

---

## 8. 推荐验收标准

- 任何用户任务最终都有 `runId`、`status`、`steps`、`trace`、`checkpoints`。
- 新增一个 Pack 不需要修改 Java `AgentGatewayService` 的角色方法。
- 前端工作台不再用静态 `initialFlowSteps` 表达真实执行状态。
- 旧 `/api/agent/{role}/chat` 仍可用，但其内部通过 Core 或兼容 Adapter 执行。
- `WorkflowRuntime` 不直接依赖法律、教师、程序员、作家等具体行业实现。
- `Core` 只在 bootstrap 处加载 Pack，运行时通过 Registry 解析。
- `TraceEvent` 成为唯一执行轨迹结构，旧 `AgentTraceStep` 只作为兼容响应。
- 模型、检索、联邦增强和 Store 都有可替换 Adapter。
- `agent/tests/test_agentos_core.py` 和现有专业体技能测试持续通过。
- 文档中不再把 `agent/app/agent_core` 当作真实路径。

---

## 9. 需要你确认的问题

1. teacher、programmer、writer 是否都要升级成完整 Workflow Pack，还是先作为“单步专业体 Pack”保留？
2. `core/packs/{packId}` 是否作为新的 Pack 根目录？我建议采用这个路径。
3. WorkflowStore 第一版是否只做 Python 内存 Adapter，还是直接接 Java/PostgreSQL？
4. 前端工作台是否优先服务“AgentOS 控制台”，还是继续兼顾联邦模型展示？
5. 旧“思维链视图”是否统一改成“执行轨迹/执行说明”？

---

## 10. 我建议的下一步实现顺序

如果按最小风险推进，下一轮建议只做三件事：

1. 新增 `WorkflowStore` Interface，把现有内存运行状态包装起来，不改变外部行为。
2. 新增 `SkillRegistry`，先让 `ToolRouter` 通过 Registry 获取技能，但保持旧专业体测试通过。
3. 新增兼容 Adapter 草案，让一个旧入口，例如 lawyer，能通过 `WorkflowRuntime` 返回旧响应。

这三步完成后，架构会从“两套平行运行时”变成“一个主运行时 + 旧入口兼容层”，后续 Java 和前端再接入就会稳很多。
