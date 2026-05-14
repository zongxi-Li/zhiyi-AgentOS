# 知弈职业智能体操作系统 TODO 蓝图

日期：2026-05-14

定位：面向专业职业场景的智能体操作系统（Agent Operating Platform）

本文用于把“知弈”从当前的多功能 AI 系统，收敛为一条清晰的主线：可治理的职业多智能体工作流平台。

> 说明：用户草案中提到的“驾驭学习”，本文统一按“驾驭工程 / Agent Harness Engineering / Agent Runtime Engineering”理解。核心不是让模型更会聊天，而是让专业 Agent 在明确任务流、状态、记忆、约束、观测和人工接管机制下稳定完成工作。

---

## 1. 最高层结论

知弈后续不应继续按“AI 功能集合”扩张，而应重构为：

```text
面向专业职业场景的可治理多智能体操作系统
```

一句话解释：

```text
让多个具备职业目标、记忆、状态和工具能力的 Agent，在 Orchestrator 驱动下，长期稳定完成专业工作流。
```

这意味着核心竞争力不再是：

- 聊天界面
- 单轮问答
- 更多模型接口
- 更多外围能力

而是：

- 职业工作流
- 多 Agent 协作
- 状态驱动编排
- 长期记忆
- 可恢复执行
- 可观测控制台
- 工作流级评估

---

## 2. 当前项目的真实位置

### 2.1 已经具备的平台雏形

当前系统已经不是普通聊天软件。现有代码中已经存在以下关键种子：

- `agent/app/agent_core/react/planner.py`：已有 ReAct Planner。
- `agent/app/agent_core/react/executor.py`：已有逐步执行与 trace 收集。
- `agent/app/agent_core/react/tool_router.py`：已有技能路由。
- `agent/app/agent_core/schema/agent_types.py`：已有 `PlannedAction`、`SkillRequest`、`SkillResult`、`AgentTraceStep`。
- `agent/app/agent_core/memory/session_memory.py`：已有会话记忆雏形。
- `agent/app/agent_core/federated/federated_adapter.py`：已有联邦增强入口。
- `frontend/src/components/agent/TraceTimeline.vue`：已有执行轨迹展示能力。
- `frontend/src/views/FederatedAgentWorkbenchView.vue`：已有工作台雏形。
- `backend/src/main/java/com/kinlin/ai/service/AgentGatewayService.java`：已有 Java 到 Python Agent 网关。
- `backend/src/main/java/com/kinlin/ai/dto/agent/AgentChatResponse.java`：已有 `skillsUsed` 和 `trace` 字段。

这些能力说明：系统已经接近“Agent Runtime”，但目前还没有形成完整的“多 Agent 协作操作系统”。

### 2.2 当前最大结构性问题

当前主要链路仍然是：

```text
职业入口 Agent
  -> Planner
  -> ToolRouter
  -> Skill
  -> 返回结果
```

这本质上仍然偏“单 Agent + 工具调用”。

目标链路应升级为：

```text
Orchestrator
  -> Workflow
  -> Professional Agent
  -> Skill / Tool / RAG / Model
  -> Checkpoint
  -> Review
  -> Final Result
```

关键变化：

- `Skill` 不再直接代表职业能力，只代表可执行工具。
- `Agent` 必须拥有目标、上下文、状态、记忆、策略和反馈。
- `Orchestrator` 必须管理任务、状态、恢复、审查和汇总。
- `Console` 必须能看见任务在哪里、为什么失败、如何恢复。

---

## 3. 宏观架构：三平面 + 七层

为了避免宏观架构混乱，后续统一采用“三平面 + 七层”的架构解释。

### 3.1 三个平面

```text
控制平面 Control Plane
  负责：任务创建、编排、状态机、恢复、人工接管、控制台。

执行平面 Execution Plane
  负责：职业 Agent、Skill、RAG、模型调用、工具执行。

治理平面 Governance Plane
  负责：记忆、可观测性、评估、权限、审计、联邦经验。
```

理解方式：

- 控制平面回答“谁来做、按什么顺序做、什么时候停”。
- 执行平面回答“具体怎么做”。
- 治理平面回答“做得是否可靠、能否恢复、是否可审计、是否能持续变好”。

### 3.2 七层架构

```text
L1 产品交互层
  Chat / RAG / Workbench / Console

L2 业务中枢层
  Java Backend：用户、会话、角色、推荐、权限、持久化、Agent 网关

L3 智能体控制层
  Python Orchestrator：任务拆解、Agent 调度、状态机、检查点、恢复

L4 职业 Agent 层
  LawyerAgent / TeacherAgent / ProgrammerAgent / WriterAgent

L5 能力执行层
  Skills / Tools / RAG / Knowledge Graph / Model Adapters

L6 记忆与经验层
  Session Memory / Workflow Memory / Career Memory / Profile Memory / Federated Memory

L7 观测评估治理层
  Trace / Metrics / Evaluation / Guardrails / Audit / Human Review
```

### 3.3 和当前代码的映射

| 目标层级 | 当前已有基础 | 当前缺口 |
|---|---|---|
| 产品交互层 | `ChatView`、`RagView`、`FederatedAgentWorkbenchView`、`RecommendationPanel` | 缺少统一任务控制台和工作流操作 |
| 业务中枢层 | Spring Boot Controller / Service / Repository | 缺少工作流运行记录、任务状态、检查点实体 |
| 智能体控制层 | `ReactPlanner`、`ReactExecutor`、`ToolRouter` | 缺少真正的 `Orchestrator`、状态机、恢复机制 |
| 职业 Agent 层 | 四个专业体 API：lawyer / teacher / programmer / writer | 当前更像角色入口，不是独立 Agent Runtime |
| 能力执行层 | 多职业 skills、RAG、模型适配器 | Skill 边界需要重新整理成工具层 |
| 记忆与经验层 | `SessionMemoryStore` | 缺少持久化 workflow memory、career memory、federated memory |
| 观测评估治理层 | `trace`、`skillsUsed`、部分 metrics | 缺少标准 trace schema、评估指标、审计与人工审核 |

---

## 4. 核心概念重新定义

### 4.1 Chat

Chat 是入口，不是目标。

TODO：

- [ ] 保留 Chat 作为轻量对话入口。
- [ ] Chat 中的复杂任务要能升级为 Workflow。
- [ ] Chat 的推荐项要引导用户进入职业工作流，而不是只推荐下一句提问。

### 4.2 Skill

Skill 是可复用的专业能力原子。

它应该具备：

- 明确输入
- 明确输出
- 可测试
- 可追踪
- 可失败
- 可被 Agent 调用

TODO：

- [ ] 给所有 Skill 建立统一 metadata：`name`、`role`、`input_schema`、`output_schema`、`risk_level`、`timeout`、`retry_policy`。
- [ ] 将 Skill 输出统一为结构化结果，不允许只返回自然语言。
- [ ] 为法律 Skill 优先补齐单元测试和样例输入输出。

### 4.3 Agent

Agent 不是 Prompt，也不是 Skill 集合。

Agent 必须拥有：

- 目标：它在工作流中负责什么。
- 状态：当前是否 idle、running、waiting、failed、completed。
- 上下文：它能看到哪些任务信息。
- 记忆：它长期保留什么经验。
- 工具：它能调用哪些 Skill。
- 评估：它如何判断自己的输出是否合格。

TODO：

- [ ] 定义 `BaseAgent` 抽象。
- [ ] 定义 `AgentProfile`：角色、目标、能力边界、风险边界。
- [ ] 定义 `AgentState`：`idle`、`planning`、`running`、`waiting`、`reviewing`、`failed`、`retrying`、`completed`。
- [ ] 先把法律方向拆成多个子 Agent：`CaseIntakeAgent`、`StatuteAgent`、`CaseRetrievalAgent`、`RiskAgent`、`DraftingAgent`、`ReviewAgent`。

### 4.4 Workflow

Workflow 是专业任务的主形态。

它不是一串 prompt，而是：

```text
目标 -> 步骤 -> Agent 调度 -> 中间产物 -> 检查点 -> 审查 -> 最终交付
```

TODO：

- [ ] 定义 `WorkflowDefinition`：工作流模板。
- [ ] 定义 `WorkflowRun`：一次实际运行。
- [ ] 定义 `WorkflowStep`：步骤、输入、输出、状态、负责 Agent。
- [ ] 定义 `Checkpoint`：步骤完成后的可恢复快照。
- [ ] 先实现法律案件工作流模板。

### 4.5 Orchestrator

Orchestrator 是整个系统的“驾驭核心”。

它不是一个更大的 LLM Prompt，而是 Agent Runtime。

职责：

- 接收任务
- 解析目标
- 选择工作流
- 拆分步骤
- 调度 Agent
- 传递上下文
- 管理状态
- 创建检查点
- 处理失败恢复
- 汇总最终结果
- 输出 trace

TODO：

- [ ] 新建 `agent/app/agent_core/orchestration/`。
- [ ] 实现 `orchestrator.py`，负责 WorkflowRun 生命周期。
- [ ] 实现 `state_machine.py`，统一任务和 Agent 状态。
- [ ] 实现 `checkpoint.py`，保存步骤级中间状态。
- [ ] 实现 `agent_registry.py`，注册可调度职业 Agent。
- [ ] 实现 `workflow_registry.py`，注册法律、教育、编程、写作工作流模板。

### 4.6 Console

Console 是驾驭工程的前端形态。

它不只是展示结果，而是让人能看见和控制运行时。

TODO：

- [ ] 在 Workbench 中展示 WorkflowRun 状态。
- [ ] 展示每个步骤的 Agent、输入、输出、耗时、状态。
- [ ] 展示 trace、checkpoint、retry、fallback。
- [ ] 增加人工审核节点：通过、驳回、重跑、终止。
- [ ] 增加失败恢复入口：从上一个 checkpoint 继续。

---

## 5. 第一条主线：法律职业闭环

后续不建议同时推进法律、教育、编程、写作四条完整闭环。第一阶段只做法律闭环。

原因：

- 法律天然多步骤。
- 法律有清晰规则、证据、法条、风险、文书。
- 法律强依赖审核机制，适合体现可治理 Agent。
- 法律结果更容易做专业评估。

### 5.1 法律工作流目标

```text
案件输入
  -> 案件拆解
  -> 法条检索
  -> 判例/类案检索
  -> 证据分析
  -> 风险评估
  -> 文书生成
  -> 审查修订
  -> 最终输出
```

### 5.2 法律子 Agent 划分

| 子 Agent | 职责 | 可复用现有 Skill |
|---|---|---|
| `CaseIntakeAgent` | 案情理解、事实要素抽取、争议焦点识别 | `case_understanding_skill.py` |
| `StatuteAgent` | 法条检索、法律依据整理 | `statute_retrieval_skill.py` |
| `CaseRetrievalAgent` | 类案检索、案例相关性判断 | `case_retrieval_skill.py` |
| `EvidenceAgent` | 证据强弱、证据链缺口、举证风险 | `evidence_analysis_skill.py` |
| `RiskAgent` | 诉讼风险、时效风险、管辖风险 | `risk_assessment_skill.py`、`limitation_calculation_skill.py`、`jurisdiction_determination_skill.py` |
| `DraftingAgent` | 文书草拟、结构化输出 | `document_generation_skill.py`、`hearing_outline_generation_skill.py` |
| `ReviewAgent` | 法条一致性、事实一致性、遗漏检查、格式审查 | 新增 |

### 5.3 法律闭环 MVP

MVP 不追求覆盖所有法律业务，只追求一个可演示、可评估、可恢复的闭环。

TODO：

- [ ] 选定第一个法律任务：民事合同纠纷初步分析。
- [ ] 固定输入格式：案情描述、证据材料、诉求、地区、时间节点。
- [ ] 固定输出格式：案情摘要、争议焦点、法律依据、类案参考、风险评估、文书草稿、审查结论。
- [ ] 每个步骤生成结构化中间产物。
- [ ] 每个步骤落 trace 和 checkpoint。
- [ ] 至少支持一个失败恢复场景：法条检索失败后重试或降级到静态规则。

---

## 6. 分阶段 TODO 路线

### Phase 0：架构收敛与冻结外围功能

目标：把系统主线从“功能集合”收敛到“职业多智能体工作流”。

TODO：

- [ ] 将 `docs/design/core.md` 作为当前架构基线。
- [ ] 将本文作为下一阶段 TODO 主文档。
- [ ] 明确暂缓项：数字人、语音、动画、多模态、通用模型训练。
- [ ] 明确当前主线：法律职业工作流、Orchestrator、状态机、控制台、评估。
- [ ] 梳理现有法律 Skill 的输入输出和可复用程度。

完成标准：

- [ ] 团队能用一张图说明三平面七层架构。
- [ ] 所有新需求都能归入某一层，不再散落堆功能。

### Phase 1：Orchestrator 最小骨架

目标：建立可运行的 Agent Runtime 骨架。

TODO：

- [ ] 创建 `agent/app/agent_core/orchestration/`。
- [ ] 定义核心类型：`AgentTask`、`WorkflowDefinition`、`WorkflowRun`、`WorkflowStep`、`Checkpoint`、`TraceEvent`。
- [ ] 实现状态机：`pending`、`planning`、`running`、`waiting_review`、`failed`、`retrying`、`completed`、`cancelled`。
- [ ] 实现最小 `Orchestrator.run()`：接收任务、选择工作流、执行步骤、返回结构化结果。
- [ ] 保留现有 `ReactPlanner` 和 `ReactExecutor`，先作为步骤内部执行器，不强行推翻。
- [ ] 新增 API：`POST /ai/orchestrate/run`。
- [ ] 新增 API：`GET /ai/orchestrate/runs/{runId}`。

完成标准：

- [ ] 一个法律工作流能按固定步骤跑完。
- [ ] 每一步都有状态、输入、输出、耗时、trace。
- [ ] 失败时能返回明确失败步骤和原因。

### Phase 2：Skill → Legal Sub-Agent

目标：把法律 Skill 包装成具备角色目标的子 Agent。

TODO：

- [ ] 新建 `agent/app/agent_core/agents/base.py`。
- [ ] 新建 `agent/app/agent_core/agents/legal/`。
- [ ] 实现 `CaseIntakeAgent`。
- [ ] 实现 `StatuteAgent`。
- [ ] 实现 `EvidenceAgent`。
- [ ] 实现 `RiskAgent`。
- [ ] 实现 `DraftingAgent`。
- [ ] 实现 `ReviewAgent`。
- [ ] 每个 Agent 暴露统一方法：`plan()`、`run()`、`review()`、`to_trace()`。

完成标准：

- [ ] Orchestrator 调度的是 Agent，不是直接调 Skill。
- [ ] Skill 仍保留，但成为 Agent 内部工具。
- [ ] 每个 Agent 有自己的输入输出 schema。

### Phase 3：Workflow Memory 与 Checkpoint

目标：让长任务可以恢复，不再依赖一次性内存。

TODO：

- [ ] 扩展内存分层：`SessionMemory`、`WorkflowMemory`、`CareerMemory`、`ProfileMemory`、`FederatedMemory`。
- [ ] 先实现 `WorkflowMemory`，保存工作流运行中的步骤产物。
- [ ] 定义 checkpoint 内容：步骤编号、Agent、输入、输出、错误、下一步建议。
- [ ] 支持从最近 checkpoint 恢复。
- [ ] Java 后端新增工作流运行记录或先由 Python 本地持久化，二选一后再实现。

建议决策：

```text
短期：Python 侧先落 WorkflowRun JSON / SQLite，降低联调成本。
中期：Java 后端接管正式业务持久化和审计。
```

完成标准：

- [ ] 人为制造某一步失败后，可以从 checkpoint 继续。
- [ ] 前端能看到历史步骤和恢复点。

### Phase 4：Workbench 控制台升级

目标：让用户真正“驾驭”工作流。

TODO：

- [ ] 在 `FederatedAgentWorkbenchView.vue` 增加 WorkflowRun 面板。
- [ ] 展示任务总状态、当前步骤、负责 Agent、耗时、风险。
- [ ] 展示步骤列表：pending / running / completed / failed / waiting_review。
- [ ] 展示 checkpoint 列表。
- [ ] 增加操作：暂停、继续、重试、从 checkpoint 恢复、终止。
- [ ] 增加人工审核节点：通过、驳回、要求重写。
- [ ] 将现有 `TraceTimeline` 接入 WorkflowRun trace。

完成标准：

- [ ] 用户不用看日志，也能理解任务跑到哪里。
- [ ] 失败后用户能在控制台选择下一步。

### Phase 5：评估体系

目标：证明系统不是“看起来强”，而是真的更稳定、更可靠。

TODO：

- [ ] 建立法律任务评测集：至少 20 个合同纠纷样例。
- [ ] 定义工作流完成率 `Task Completion Rate`。
- [ ] 定义 `AWS`：Agent Workflow Stability。
- [ ] 定义 `ACS`：Agent Collaboration Score。
- [ ] 定义 `PWS`：Professional Workflow Score。
- [ ] 定义恢复成功率：`Recovery Success Rate`。
- [ ] 定义人工修改率：`Human Revision Rate`。
- [ ] 设计对照实验：普通 GPT、单 Agent、无状态多 Agent、有状态可治理多 Agent。

核心指标建议：

```text
TCR = 完整完成全部步骤的任务数 / 总任务数
RecoveryRate = 成功恢复次数 / 触发恢复次数
LoopRate = 重复调用或循环任务数 / 总任务数
ACS = 任务接续正确性、上下文一致性、冲突率的综合得分
PWS = 法条准确率、类案相关性、风险完整性、文书规范性的综合得分
```

完成标准：

- [ ] 能输出一张对照表证明系统改进。
- [ ] 能定位失败来自规划、Agent、Skill、检索、模型还是上下文传递。

### Phase 6：联邦记忆与推荐调度

目标：让联邦能力落在现实有效的位置。

TODO：

- [ ] 不做大模型联邦训练。
- [ ] 联邦优先用于推荐排序、Agent 调度、Skill 选择、职业偏好。
- [ ] 定义 `FederatedExperience`：匿名经验模式，不存原始案情。
- [ ] 汇总高频失败模式：例如证据缺失、时效不明、管辖冲突。
- [ ] 将推荐系统从“下一问推荐”升级为“下一步工作流动作推荐”。
- [ ] 用联邦统计辅助 Orchestrator 选择更稳的 Agent 或步骤顺序。

完成标准：

- [ ] 推荐项可以解释为什么建议下一步。
- [ ] 调度策略可以根据历史稳定性调整。
- [ ] 不泄露用户原始内容。

### Phase 7：产品化与企业化

目标：让系统具备私有部署、审计、安全和持续运营能力。

TODO：

- [ ] 定义权限：谁可以创建、查看、恢复、终止工作流。
- [ ] 定义审计日志：任务创建、Agent 调用、人工审核、恢复、导出。
- [ ] 定义数据分级：用户数据、工作流中间产物、联邦经验、评估数据。
- [ ] 增加租户隔离设计。
- [ ] 为国产 OS / 私有化部署保留配置项，但不作为当前主线开发。
- [ ] 输出企业部署清单。

完成标准：

- [ ] 系统可以解释“谁在什么时候让哪个 Agent 做了什么”。
- [ ] 工作流结果可以审计、复盘、导出。

---

## 7. 文件级 TODO 落点

### 7.1 Python Agent 服务

TODO：

- [ ] 新建 `agent/app/agent_core/orchestration/__init__.py`。
- [ ] 新建 `agent/app/agent_core/orchestration/types.py`。
- [ ] 新建 `agent/app/agent_core/orchestration/state_machine.py`。
- [ ] 新建 `agent/app/agent_core/orchestration/orchestrator.py`。
- [ ] 新建 `agent/app/agent_core/orchestration/checkpoint.py`。
- [ ] 新建 `agent/app/agent_core/orchestration/workflow_registry.py`。
- [ ] 新建 `agent/app/agent_core/agents/base.py`。
- [ ] 新建 `agent/app/agent_core/agents/legal/*.py`。
- [ ] 新建 `agent/app/api/orchestrator.py`。
- [ ] 修改 `agent/app/main.py` 注册 orchestrator 路由。
- [ ] 保留 `agent/app/agent_core/react/*`，先作为 Agent 内部规划执行工具。

### 7.2 Java 后端

TODO：

- [ ] 新增 `WorkflowController` 或 `AgentWorkflowController`。
- [ ] 新增 `WorkflowService`，代理 Python Orchestrator API。
- [ ] 新增 DTO：`WorkflowRunRequest`、`WorkflowRunResponse`、`WorkflowStepResponse`、`CheckpointResponse`。
- [ ] 后续新增实体：`WorkflowRunEntity`、`WorkflowStepEntity`、`WorkflowCheckpointEntity`。
- [ ] 将 `AgentConversationPersistenceService` 扩展为能持久化工作流摘要。
- [ ] 将 `RecommendationService` 接入工作流上下文，推荐下一步动作。

### 7.3 前端

TODO：

- [ ] 新增 `frontend/src/services/api/workflow.ts`。
- [ ] 新增 `frontend/src/stores/workflow.ts`。
- [ ] 升级 `frontend/src/views/FederatedAgentWorkbenchView.vue` 为工作流控制台。
- [ ] 复用 `frontend/src/components/agent/TraceTimeline.vue`。
- [ ] 新增 `WorkflowStepList.vue`。
- [ ] 新增 `CheckpointPanel.vue`。
- [ ] 新增 `AgentStateBadge.vue`。
- [ ] 新增 `HumanReviewPanel.vue`。
- [ ] 将 `RecommendationPanel` 扩展为支持 `targetAction = WORKFLOW_STEP`。

### 7.4 文档

TODO：

- [ ] `docs/design/core.md` 保持为当前系统层次说明。
- [ ] 本文保持为下一阶段 TODO 蓝图。
- [ ] 后续新增 `docs/design/legal-workflow-mvp.md`。
- [ ] 后续新增 `docs/design/orchestrator-state-machine.md`。
- [ ] 后续新增 `docs/design/agent-workflow-metrics.md`。

---

## 8. 关键数据模型草案

### 8.1 WorkflowRun

```text
WorkflowRun
  runId
  workflowType
  title
  userId
  conversationId
  status
  currentStepId
  steps
  checkpoints
  trace
  createdAt
  updatedAt
```

### 8.2 WorkflowStep

```text
WorkflowStep
  stepId
  runId
  name
  agentName
  status
  input
  output
  error
  startedAt
  completedAt
  retryCount
```

### 8.3 AgentNode

```text
AgentNode
  agentName
  role
  goal
  state
  allowedSkills
  memoryScope
  riskLevel
  evaluator
```

### 8.4 Checkpoint

```text
Checkpoint
  checkpointId
  runId
  stepId
  stateSnapshot
  outputSnapshot
  canResume
  createdAt
```

### 8.5 TraceEvent

```text
TraceEvent
  eventId
  runId
  stepId
  agentName
  eventType
  thought
  action
  observation
  durationMs
  error
```

---

## 9. 优先级矩阵

### S 级：必须立刻聚焦

- [ ] Orchestrator
- [ ] 法律职业工作流
- [ ] 多 Agent 状态机
- [ ] Workflow Memory
- [ ] Checkpoint 与恢复
- [ ] Workbench 控制台
- [ ] 工作流评估指标

### A 级：紧随其后

- [ ] RAG 增强
- [ ] 推荐系统升级为下一步动作推荐
- [ ] Skill schema 标准化
- [ ] 用户画像
- [ ] Agent 调度策略

### B 级：后续增强

- [ ] 数字人
- [ ] 语音
- [ ] 动画
- [ ] 多模态
- [ ] 国产 OS 细节优化

### C 级：暂缓

- [ ] 自训练大模型
- [ ] 大规模蒸馏
- [ ] 通用底层模型训练
- [ ] 大规模联邦训练 LLM

---

## 10. 最小可交付版本

最小可交付版本不是“大而全平台”，而是：

```text
一个可运行、可观测、可恢复、可评估的法律多 Agent 工作流。
```

MVP 包含：

- [ ] 一个入口：Workbench 发起法律工作流。
- [ ] 一个 Orchestrator：按固定模板调度。
- [ ] 六个法律子 Agent：案件、法条、类案、证据、风险、文书/审查。
- [ ] 一个状态机：每步状态可见。
- [ ] 一个 checkpoint 机制：至少支持失败恢复。
- [ ] 一个 trace 面板：每步动作可回放。
- [ ] 一个评估脚本：输出完成率、稳定性、恢复率。

MVP 不包含：

- [ ] 多行业完整闭环。
- [ ] 大规模联邦训练。
- [ ] 复杂多模态。
- [ ] 数字人深度接入。
- [ ] 完整企业权限体系。

---

## 11. 近期 10 个具体 TODO

按顺序执行：

- [ ] 1. 审阅并确认本文的宏观架构是否作为后续主线。
- [ ] 2. 冻结非主线功能开发，避免继续扩散。
- [ ] 3. 梳理法律 Skill 输入输出，形成 `legal-skill-inventory.md`。
- [ ] 4. 设计 `WorkflowRun`、`WorkflowStep`、`Checkpoint`、`TraceEvent` 类型。
- [ ] 5. 实现 Python `orchestration` 目录和最小 Orchestrator。
- [ ] 6. 把 `case_understanding_skill.py` 包装成第一个 `CaseIntakeAgent`。
- [ ] 7. 跑通固定法律工作流的前 3 步：案情拆解、法条检索、证据分析。
- [ ] 8. 在 Workbench 展示 WorkflowRun 步骤状态。
- [ ] 9. 增加一个可恢复失败场景。
- [ ] 10. 建立第一批 20 个法律样例，开始计算工作流完成率。

---

## 12. 最终判断

知弈真正应该争夺的不是“更会聊天”，而是“更能稳定完成专业工作”。

因此后续主线应明确为：

```text
职业多智能体系统
  -> Orchestrator 编排
  -> 法律职业工作流 MVP
  -> 状态驱动协作
  -> 长期记忆与 checkpoint
  -> 控制台可观测
  -> 工作流级评估
  -> 联邦经验共享
```

当这条链路跑通后，系统才真正从“工具调用系统”进入“专业智能体操作系统”。
