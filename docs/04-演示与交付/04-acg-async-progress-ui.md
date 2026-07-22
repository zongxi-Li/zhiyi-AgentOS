# ACG Phase 4：异步启动与前端进度闭环

## 链路

```text
User
 -> AcgVisualizationView
 -> Java POST /api/agentos/core/workflows/start-async
 -> Python POST /ai/core/workflows/start-async
 -> prepare_run / coordinator.submit
 -> runId
 -> useWorkflowProgress
 -> Java GET /api/agentos/core/workflows/runs/{runId}/progress
 -> Python ProgressAssembler
```

Java 只承担网关和契约校验，前端不配置 Python 地址。异步启动使用独立的 15 秒网关超时，保留 Python 的 `202`、`409` 和 `503` 状态。

## 前端状态语义

`understanding`、`planning` 和 `graph_building` 在 `percent=null` 时使用不定长进度条；不显示 `0%`。`executing`、`recovery`、`review`、`completed`、`failed` 和 `cancelled` 使用 ProgressAssembler 返回的真实百分比。`review` 继续轮询，只有后三种终态停止轮询。

`useWorkflowProgress` 负责立即首查、2 秒单飞轮询、短暂错误退避、有限的启动期 404 重试、终态回调和卸载取消。generation、当前 runId 和 AbortController 同时保护旧响应。`updatedAt` 不变化仍是成功响应，不会被判定为卡死。

## ACG 请求分频

| 请求 | 频率 |
| --- | --- |
| Progress | 首次立即，之后 2 秒 |
| 完整 ACG、Run、血缘、指标、交付物 | 执行/恢复/审核阶段最多每 8 秒，且仅在 `updatedAt` 变化时刷新 |
| 终态数据 | completed/failed/cancelled 强制刷新一次 |

规划阶段不请求完整拓扑。Run ID 写入 `?runId=`，刷新页面只恢复轮询，不会重新启动工作流；历史 Run 的 404 会停止并提示“运行记录不存在或当前账户无权访问”。

## 错误边界

- 启动没有可靠 runId：`任务未能启动`。
- Python 409：`相同请求标识已用于不同参数，请重新发起任务`。
- Progress 临时网络错误：保留最后状态并显示`进度同步暂时中断，正在重试`。
- `phase=failed` 才是工作流失败；网络错误不会把运行改成 failed。
