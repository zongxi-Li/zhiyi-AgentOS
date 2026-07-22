# ACG Progress 查询契约

Phase 3 建立从持久化 `WorkflowRun` 到前端可调用 HTTP 契约的只读查询链路：

```text
WorkflowRun Store -> ProgressAssembler -> Python FastAPI -> Java AgentOS Gateway
```

本阶段不修改 Vue 页面、前端状态管理、SSE 或 WebSocket。

## 路径

Python AgentOS 内部路径：

```http
GET /ai/core/workflows/runs/{runId}/progress
```

Java 网关对前端暴露的路径：

```http
GET /api/agentos/core/workflows/runs/{runId}/progress
```

Java 网关沿用现有 JWT、内部服务令牌和可信用户上下文转发。前端不得绕过 Java 直接访问 Python。

## 响应

接口直接返回 `WorkflowProgress`，不重新计算任何字段：

```json
{
  "taskId": "task_xxx",
  "runId": "run_xxx",
  "workflowId": "legal_contract_review_v1",
  "status": "running",
  "phase": "executing",
  "message": "正在执行步骤：risk_detect",
  "percent": 42.86,
  "totalSteps": 7,
  "pendingSteps": 3,
  "runningSteps": 1,
  "waitingReviewSteps": 0,
  "retryingSteps": 0,
  "failedSteps": 0,
  "completedSteps": 3,
  "cancelledSteps": 0,
  "currentStepId": "risk_detect",
  "activeStepIds": ["risk_detect"],
  "recoveryCount": 0,
  "startedAt": "2026-07-22T01:06:26Z",
  "updatedAt": "2026-07-22T01:07:20Z",
  "progress": 0.4286,
  "percentage": 42.86
}
```

Java 使用强类型 `WorkflowProgressResponse`，`percent` 使用可空 `BigDecimal`，时间保持 ISO-8601，`activeStepIds` 顺序原样保留。

## Phase 与 percent

| phase | 含义 | percent |
|---|---|---|
| `understanding` | Run 已创建，尚无确定步骤规模 | `null` |
| `planning` | Planner 执行中 | `null` |
| `graph_building` | Blueprint 和步骤正在构建 | `null` |
| `executing` | 已确定步骤规模，按 completedSteps/totalSteps 投影 | `0..100` |
| `recovery` | 节点重试或恢复 | 当前真实比例 |
| `review` | 等待人工审核 | 当前真实比例 |
| `completed` | 工作流完成 | `100` |
| `failed` | 工作流失败 | 已完成步骤的真实比例 |
| `cancelled` | 工作流取消 | 已完成步骤的真实比例 |

`progress` 是兼容字段，范围为 `0..1`；`percentage` 是兼容字段，范围为 `0..100`。新调用方必须优先使用 `percent`，不得把 `null` 转换成 `0`。

## HTTP 语义

| 情况 | 状态码 |
|---|---:|
| Run 存在，包括 pending、running、review、completed、failed、cancelled | `200` |
| Run 不存在，或当前可信用户不拥有带归属信息的 Run | `404` |
| Python Store 暂不可用 | `503` |
| Python 返回缺字段或不支持的 phase | Python `500`，Java 返回安全的 `502` |

Progress 查询不会启动 Planner/Executor，不读取完整 Trace、Checkpoint、Artifact，也不会更新 Run 或生成新的 `updatedAt`。

## 权限边界

Java 网关要求现有 JWT 认证，并通过内部请求头传递用户和 tenant 上下文。Python 对 Phase 2 之后写入 `authenticatedUserId` 的 Run 执行同用户、同 tenant 校验；不匹配时统一返回 404。没有归属元数据的历史 Run 保持既有网关边界，当前风险是历史数据无法做细粒度归属校验。

## 轮询建议

Phase 4 前端可以在拿到异步启动接口返回的 `runId` 后轮询 Java 路径。建议间隔为 `1.5-2.5s`，终态为 `completed`、`failed` 或 `cancelled` 时停止。前端可用 `updatedAt` 判断是否有真实状态变化。

Progress 查询使用独立轻量超时，默认 `5000ms`，配置项为 `AGENT_PROGRESS_TIMEOUT_MS`；不会复用工作流启动和模型执行的长超时。

## 性能边界

Python 每次查询执行一次 Store `get_run` 和一次 `ProgressAssembler.assemble`，投影复杂度为 `O(steps)`，不产生 N+1 查询。1000 steps 的本地测试约为纯投影 `0.3ms`、API `11ms`；该数字仅是本地证据，不构成跨环境 SLA。
