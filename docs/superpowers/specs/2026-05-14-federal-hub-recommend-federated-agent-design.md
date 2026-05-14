# 联邦智枢 Recommend 融合与联邦智能体方案设计

> 目标：把现有 `Recommend` 推荐能力接入当前前后端，同时把现有 Skill/Agent 体系升级为可编排、可恢复、可评估的联邦智能体运行时。

## 结论先行
- 这不是重建一个新系统，而是把现有三层架构收拢成一个统一运行时。
- `Recommend` 最适合放在“交互层推荐引擎”里，负责引导下一步提问、动作和角色切换。
- “联邦智枢”的核心不是训练更大的底座模型，而是编排多个职业 Agent，并把联邦学习用于推荐、排序、调度和偏好学习。

## 1. 现状判断
- 根仓库已经有 `frontend`、`backend`、`agent` 三层。
- `backend/src/main/java/com/kinlin/ai/controller/RecommendationController.java` 和 `service/RecommendationService.java` 已存在。
- `frontend/src/services/api/recommendation.ts` 已存在，但 `ChatView` 和 `chat.ts` 目前没有真正接入推荐链路。
- `agent/app` 已经有 `ReactPlanner`、`ToolRouter`、`FederatedAdapter` 和多职业 skills。
- 当前工作区扫描里，`Recommend/` 没有看到可直接迁移的主源代码，更像概念来源或残留工作区，不应按独立主仓库处理。

## 2. 需要解决的两件事
- 推荐怎么融入现有产品。
- 新智能体方案怎么落到工程里。

## 3. Recommend 融合方案
### 3.1 角色定位
`Recommend` 不做独立页面，也不做独立业务线，定位为“对话与任务的下一步建议层”。

### 3.2 前端接入点
- `frontend/src/views/ChatView.vue`：空状态、发送框下方、助手回复后展示推荐。
- `frontend/src/stores/chat.ts`：在消息更新后触发推荐拉取。
- `frontend/src/components/`：新增一个轻量 `RecommendationStrip` 或 `SuggestionPanel`。
- `frontend/src/views/RagView.vue`、`FederatedAgentWorkbenchView.vue`：复用同一套推荐数据，只换展示场景。

### 3.3 后端接入点
- 继续保留 `POST /recommendations/questions` 作为基础接口。
- 推荐服务从“关键词匹配”升级为“上下文评分 + 角色偏好 + 页面场景”。
- 推荐项输出不只是一句问题，还要带 `text`、`reason`、`targetAction`、`confidence`、`scope`。

### 3.4 推荐数据流
`用户输入 -> 聊天/页面上下文 -> 推荐服务 -> 推荐列表 -> 前端快捷动作 -> 二次输入/页面跳转`

### 3.5 推荐策略
- 对话为空时返回角色默认推荐。
- 对话进行中时结合最近消息、角色、知识库命中、页面上下文生成推荐。
- 服务失败时必须 fail-open，退回静态推荐，不能阻塞主对话。

## 4. 联邦智枢智能体方案
### 4.1 总体分层
- 基础模型层：DeepSeek、Qwen 等底座模型。
- 专业智能体层：Lawyer、Teacher、Programmer、Writer。
- 协作编排层：Orchestrator，负责任务拆解、调度、状态、恢复、汇总。
- 用户生态层：推荐、画像、联邦记忆、偏好学习、权限与审计。

### 4.2 核心变化
- 现在的 `Skill` 先保留，但不再是终点。
- `Skill` 会变成 Agent 内部的可执行工具，Agent 负责目标、上下文、记忆和结果整合。
- `ToolRouter` 继续做技能路由，但真正的任务推进由 Orchestrator 负责。

### 4.3 Orchestrator 职责
- 解析用户意图。
- 拆分任务步骤。
- 选择职业 Agent 或子技能。
- 管理状态机：`idle`、`planning`、`running`、`waiting`、`reviewing`、`failed`、`completed`。
- 处理 checkpoint、重试、回滚和结果合并。

### 4.4 记忆分层
- `Session Memory`：当前会话。
- `Workflow Memory`：当前工作流步骤和中间结果。
- `Profile Memory`：用户偏好、角色倾向、常用风格。
- `Federated Memory`：跨用户、跨组织的匿名经验统计，只共享模式，不共享原始数据。

### 4.5 联邦的正确落点
- 推荐排序。
- Agent 调度优化。
- Skill 选择优化。
- 用户偏好学习。
- 职业任务完成质量评估。

## 5. 建议的数据对象和接口
### 5.1 建议对象
- `RecommendationItem`
- `AgentTask`
- `AgentTaskStep`
- `AgentPlan`
- `AgentTrace`
- `WorkflowState`

### 5.2 建议接口
- `POST /ai/orchestrate/run`
- `GET /ai/orchestrate/tasks/{taskId}`
- `POST /recommendations/contextual`

## 6. 推荐的开发顺序
### Phase 1：把 Recommend 接进主交互链路
- 后端扩展推荐返回结构。
- 前端增加推荐展示组件。
- 在 Chat、RAG、Workbench 三个入口统一接入。

### Phase 2：引入 Orchestrator
- 在 `agent/app` 增加编排层。
- 把现有四个职业 Agent 变成可调度节点。
- 把状态机和 trace 打通到前端。

### Phase 3：接入联邦记忆
- 先做推荐和调度优化，不碰底座模型训练。
- 只共享聚合结果和模式统计。

### Phase 4：评估与治理
- 增加工作流完成率、长任务稳定率、恢复成功率、协作成功率。
- 保留人工接管和降级路径。

## 7. 风险控制
- 不要把推荐做成第二套聊天输出，避免信息重复。
- 不要先做大规模联邦训练，成本高且收益不稳定。
- 不要把 Orchestrator 写成“更大的 Prompt”，它必须是状态机。
- 所有新能力都要 fail-open，不能拖垮主对话。

## 8. 文件级落点
- `frontend/src/views/ChatView.vue`：推荐展示与交互入口。
- `frontend/src/stores/chat.ts`：消息变化后触发推荐拉取。
- `frontend/src/services/api/recommendation.ts`：扩展推荐返回结构。
- `backend/src/main/java/com/kinlin/ai/service/RecommendationService.java`：从关键词规则升级为上下文评分。
- `backend/src/main/java/com/kinlin/ai/controller/RecommendationController.java`：保留基础接口，增加上下文推荐接口。
- `agent/app/agent_core/react/tool_router.py`：保留技能路由，不承担编排职责。
- `agent/app/api/*.py`：承载 Orchestrator 的对外入口。
- `agent/app/agent_core/memory/*`：承载会话、工作流、画像、联邦记忆。
- `frontend/src/views/FederatedAgentWorkbenchView.vue`：显示编排状态、trace 和恢复信息。

## 9. 最终建议
- `Recommend` 先做“对话引导层”。
- “联邦智枢”再做“可编排职业 Agent 层”。
- 先跑通一个职业闭环，再扩到多职业协同。
