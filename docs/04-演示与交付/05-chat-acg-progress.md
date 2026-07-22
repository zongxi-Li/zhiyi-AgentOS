# ACG Phase 5：Chat 实时进度闭环

## 数据流

```text
User
 -> ChatView
 -> Java start-async
 -> runId
 -> ChatWorkflowBinding
 -> useWorkflowProgress
 -> WorkflowProgressBar
 -> terminal result load
```

Chat 文本流与 Workflow 运行流保持独立。Chat SSE 继续管理文本 `content_delta`、reasoning 展示和自己的 AbortController；Workflow Progress 只管理 ACG 生命周期。任一数据流失败都不会修改另一条数据流的状态。

## 运行关联

每个新 Run 保存以下关联：

- `conversationId`：路由 `contextId`、Chat store context 或稳定的 draft ID；
- `messageId`：触发升级的用户消息；
- `taskId`、`runId`、`workflowId`：异步启动响应及请求工作流；
- `clientRequestId`：一次提交操作的幂等键；
- `createdAt`、`status`：恢复和单活动 Run 判定。

Binding 保存在现有 Chat Pinia store，并写入 `localStorage`。当前选中 Run 同时写入 `?runId=`。同一 conversation 只允许一个非终态 Run；终态后允许新运行，历史 Binding 不删除。

## 恢复与请求策略

刷新或切换 conversation 时，优先从该 conversation 的 Binding 恢复，其次使用 route runId。恢复只启动 Progress，不调用 start-async。切换会停止旧轮询、abort 旧请求，但不取消后端 Workflow。

| 请求 | 策略 |
| --- | --- |
| Progress | 首次立即，之后每 2 秒，由 `useWorkflowProgress` 单飞执行 |
| 完整 Run/ACG | 展开预览、首次进入 review 或 terminal 时读取 |
| terminal 结果 | 每个 Run 成功加载一次并缓存 |

Chat 不再每 2.5 秒轮询完整 ACG。404 会使 Binding 标记失效，不自动创建新 Run。

## 幂等与错误

提交前将 `clientRequestId` 与 conversation、文本写入 `sessionStorage`。503 或网络失败后再次提交相同文本会复用 ID 和原用户消息；成功或 409 后清除待提交记录。

- 启动失败：`ACG 任务未能启动`；
- 409：`本次请求标识与原任务参数冲突，请重新发起`；
- 503/网络：`ACG 任务暂时不可用，请稍后重试`；
- Progress 临时失败：保留最后状态并继续重试；
- Workflow failed：只由后端 `phase=failed` 触发，不删除 Chat 内容。
