# 知弈 Python Agent

`agent/` 是 Python FastAPI 应用层，负责暴露 AI 服务入口、加载行业 Pack、承载 LLM Gateway、Evidence Retriever 和 AgentOS Core API。AgentOS Core 的源码位于仓库根目录的 `agentOS/src/agentos/`。

## 当前职责

- FastAPI 应用入口：`agent/app/main.py`
- AgentOS Core API：`agent/app/api/agentos_core.py`
- Legal Pack：`agent/packs/legal/`
- 合同审查 workflow definition：`agent/packs/legal/workflows/contract_review.yaml`
- LangGraph 合同审查实现：`agent/app/graphs/contract_review/`（`legal_contract_review_stategraph.py` 仅保留兼容 shim）
- LLM Gateway：`agent/app/llm/`
- keyword Evidence Retriever：`agent/app/rag/providers/keyword_retriever.py`

AgentOS Core 不是 LangGraph。当前 Runtime 会根据 workflow definition 的 `runtimeEngine` 选择 Execution Adapter，合同审查通过 `LangGraphAdapter` 执行。

## 当前 Workflow

```text
id: legal_contract_review_v1
runtimeEngine: langgraph
implementationId: legal_contract_review_stategraph_v1
aliases:
  - legal_contract_review_stategraph_v1
  - legal_contract_review_langgraph_v1
```

artifacts 契约：

```text
risks: output.artifacts.risk_detect.risks
evidences: output.artifacts.legal_evidence_match.evidences
report: output.artifacts.report_generate.report_markdown
```

## 启动

在 `agent/` 目录运行：

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

健康检查：

```bash
curl http://localhost:8000/health
```

## 测试

在 `agent/` 目录运行：

```bash
python -m pytest tests
```

## 主要 API

通过 Spring Boot Gateway 访问时，前端主要使用 `/ai/core/**`。Python Agent 直接暴露同名 AgentOS Core API：

```text
POST /ai/core/tasks
GET  /ai/core/tasks
POST /ai/core/workflows/runs
POST /ai/core/workflows/start
GET  /ai/core/workflows/runs
GET  /ai/core/workflows/metrics
GET  /ai/core/workflows/runs/{runId}
GET  /ai/core/workflows/runs/{runId}/checkpoints
GET  /ai/core/workflows/runs/{runId}/trace
GET  /ai/core/workflows/runs/{runId}/reviews
POST /ai/core/workflows/runs/{runId}/reviews
POST /ai/core/workflows/runs/{runId}/resume
POST /ai/core/workflows/runs/{runId}/cancel
```

不恢复旧 V0.7 合同审查专用 API。律师合同审查工作台也走统一的 AgentOS Core workflow API。

## 能力边界

当前 Evidence 是演示级本地知识库 + keyword 检索，不是完整法律法规库、案例库或正式法律 RAG。当前报告不是正式法律意见，需要律师复核。

## V1.0.6 代码边界

- AgentOS Core 不直接 import `app.*`、`app.graphs.*` 或 `langgraph`。
- `LangGraphAdapter` 位于应用层 `agent/app/execution/`。
- `LangGraphImplementationRegistry` 负责将 `implementationId` 映射到具体 StateGraph runtime。
- 合同审查 StateGraph 主体位于 `agent/app/graphs/contract_review/`。
- `graph.py` 只负责图拓扑，`nodes/*` 负责节点逻辑，`projector.py` 负责投影回 AgentOS `WorkflowRun`。
- `artifacts.py` 负责稳定 artifact 路径契约。
- `agent/app/graphs/legal_contract_review_stategraph.py` 仅作为兼容 shim 保留。
- Core 侧 `model_adapter.py` 只保留模型协议和注册入口，具体 `app.services.aiservice.AIService` 由 `agent/app/integrations/model_adapter.py` 注册。
