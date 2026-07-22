# Phase 6：AgentOS 全局运行控制面

## 审查结论

`AgentOsConsoleView` 原本已经有运行列表、完整 Run 详情、Trace、Checkpoint 和 HumanReviewPanel，但列表直接返回完整 `WorkflowRun`，选中 Run 后立即并行读取 Trace、Checkpoint、Review 和指标；Review 仅由页面按钮禁用保护，缺少 expected state、operation ID 和 409 语义。Chat 与角色工作台也各自直接调用 Review API。

本阶段复用既有 `/core/workflows/runs`、Progress、Run、ACG、Reviews 和 Resume 端点，列表增加 `summary=true`、`statuses`、`taskId`、`lifecyclePhase` 和有界分页参数。Java 只补充这些查询参数的可信转发；Python 在同一 WorkflowRun Store 上做权限过滤和 summary 投影，没有新数据库或新执行器。

## 全局数据流

```text
Chat / ACG / Console
        |
        v
Workflow Run Store（客户端索引，不是真相）
        |
        +-- Progress API（选中 Run，2 秒单飞）
        +-- Run List API（Console，7 秒单请求）
        +-- Review API（共享 operationId + expected state）
        |
        v
Python WorkflowRun Store / Executor
```

## 恢复与索引

- URL `runId` 优先用于当前页面选中 Run；
- `workflow.run.references.v1` 只保存 Run 引用、来源和 Chat 导航字段；
- Phase 5 的 `chat.workflow_bindings.v1` 保留不删除，并在 Store 初始化时兼容读取；
- 应用启动只请求一次有界非终态 summary 列表，不为所有 Run 开 Progress；
- 后端状态覆盖本地旧状态，本地仅补充 `conversationId/messageId/source/lastSeenAt`；
- 404 标记 invalid，不自动重启；完整 Run、Trace、ACG 和 Artifact 不进入 Store。

## 列表与详情策略

Console 默认一次请求最多 50 条，服务端按“待审核→运行中→最近终态”排序并分页。可见时 7 秒刷新；页面隐藏暂停，恢复可见立即刷新。列表不为每个 Run 建立定时器，只有当前选中 Run 使用共享 `useWorkflowProgress` 的 2 秒单飞轮询。

完整 Run/Trace/Checkpoint/Review/ACG 仅在用户展开详情、首次进入 review 或首次进入终态时加载；终态详情只在当前页面生命周期缓存一次。

## 统一审核

`WorkflowReviewPanel` 与 `useWorkflowReview` 被 Chat、ACG、Console 共用。请求沿用既有 Reviews 端点，并附带：

```json
{
  "decision": "approved",
  "operationId": "review-operation-id",
  "expectedRunUpdatedAt": "...",
  "expectedStepStatus": "waiting_review"
}
```

Python Runtime 对同一 Run 串行化审核，确认 Run/Step 仍为 `waiting_review`，重复 operation ID 返回当前结果，状态或 revision 不一致返回 409。审核后前端只刷新 Progress 和必要详情，不把结果写死为 completed。当前可信身份来自 Java→Python Trusted User Context；带归属字段的 Run 执行用户/租户隔离，历史无归属 Run 仍按现有兼容边界处理。

## 页面职责

- Chat：当前会话紧凑 Progress、紧凑审核入口、ACG/Console 导航，Chat SSE 生命周期不变；
- ACG：拓扑、详细 Progress、详细审核、血缘/审查数据，并可返回关联 Chat；
- Console：全局列表、选中 Run 详情、统一 Review、ACG/Chat 导航。

## Phase 7 保留

Progress SSE、polling/SSE fallback、Last-Event-ID、标签页协调、BroadcastChannel、动态拓扑增量事件、全局通知和后台完成提醒均未实现。
