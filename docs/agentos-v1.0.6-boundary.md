# AgentOS V1.0.6 边界说明

本文记录 V1.0.6 后的真实代码边界，用于后续进入 V1.0-beta 前校准架构口径。

## 1. Core 边界

`agentOS/src/agentos/` 是 AgentOS Core 与通用框架层。Core 的职责是治理主线，而不是具体业务实现：

- `WorkflowRuntime` 负责 Task / WorkflowRun 生命周期推进。
- `TraceStore`、`CheckpointStore`、`ReviewManager` 负责治理对象。
- `WorkflowRegistry`、`TaskManager`、`Orchestrator` 负责 native workflow 控制面。
- `ExecutionAdapter` 协议定义外部执行引擎如何接入 Core。
- `ModelAdapter` 只保留模型服务协议、注册入口和兼容代理。

Core 不应直接依赖以下内容：

- `app.*`
- `app.services.*`
- `app.graphs.*`
- `langgraph`
- 具体业务 workflow 或具体 StateGraph

## 2. LangGraph 接入位置

LangGraph 不在 AgentOS Core 内。当前 LangGraph 接入位于应用层：

```text
agent/app/execution/
  langgraph_adapter.py
  langgraph_registry.py
  runtime.py
```

`LangGraphAdapter` 负责把 `runtimeEngine: langgraph` 的 workflow 交给应用层 StateGraph runtime。`LangGraphImplementationRegistry` 负责将 `implementationId` 映射到具体实现：

```text
legal_contract_review_stategraph_v1
  -> LegalContractReviewStateGraphRuntime
```

## 3. 合同审查 StateGraph 结构

合同审查业务图已经拆分为独立包：

```text
agent/app/graphs/contract_review/
  graph.py
  state.py
  runtime.py
  projector.py
  artifacts.py
  mock_data.py
  nodes/
    parse_contract.py
    classify_clauses.py
    risk_detect.py
    legal_evidence_match.py
    suggestion_generate.py
    human_review.py
    report_generate.py
```

职责划分：

- `graph.py` 只负责 StateGraph 拓扑：`add_node`、`add_edge`、`compile(checkpointer, interrupt_before=["report_generate"])`。
- `state.py` 只负责 `ContractReviewState`、`WORKFLOW_ID` 和步骤序列。
- `nodes/*` 负责各节点业务逻辑、能力调用、artifact 写入和 trace/step 更新。
- `artifacts.py` 负责 artifact key 和路径契约。
- `projector.py` 负责将 LangGraph State 投影回 AgentOS 标准 `WorkflowRun`，同步 steps、`run.output`、Trace、Checkpoint。
- `runtime.py` 负责把合同审查 StateGraph 暴露成 AgentOS 可调用的 runtime，并保持 Human Review 行为。
- `mock_data.py` 保留本地 fallback 数据。
- `legal_contract_review_stategraph.py` 只是兼容 shim，不再承载主体逻辑。

## 4. 稳定契约

对外 canonical workflow id 保持不变：

```text
legal_contract_review_v1
```

内部 implementation id 保持不变：

```text
legal_contract_review_stategraph_v1
```

兼容 aliases 保持不变：

```text
legal_contract_review_stategraph_v1
legal_contract_review_langgraph_v1
```

artifact 路径保持不变：

```text
risks:     output.artifacts.risk_detect.risks
evidences: output.artifacts.legal_evidence_match.evidences
report:    output.artifacts.report_generate.report_markdown
```

Human Review 行为保持不变：

```text
approved       -> resume 到 report_generate，并生成 report_markdown
rejected       -> run failed，不生成 report_markdown
need_more_info -> 保持 waiting_review，不生成 report_markdown
```

## 5. 模型适配边界

`agentOS/src/agentos/adapters/model_adapter.py` 不再懒加载 `app.services.aiservice`。Core 侧只保留：

- `ModelService` Protocol
- `ModelServiceFactory`
- `register_model_service_factory`
- `clear_model_service_factory`
- 兼容代理 `AIService`
- 薄包装 `ModelAdapter`

应用层通过以下文件注册具体实现：

```text
agent/app/integrations/model_adapter.py
```

FastAPI 应用启动模块会调用 `configure_model_adapter()`，将 `app.services.aiservice.AIService` 注册给 AgentOS 的模型代理。这样 Pack skill 仍可继续使用 `agentos.adapters.model_adapter.AIService()`，但 Core 不再反向依赖 app 层。

## 6. 当前演示链路

```text
律师合同审查工作台
  -> Spring Boot Gateway
  -> Python AgentOS Core API
  -> WorkflowRuntime 启动 legal_contract_review_v1
  -> app.execution.LangGraphAdapter
  -> LangGraphImplementationRegistry
  -> legal_contract_review_stategraph_v1
  -> contract_review StateGraph
  -> Human Review
  -> approved 后生成 report_markdown
  -> AgentOS Console 查看 WorkflowRun / Trace / Checkpoint / Review
```

当前仍是演示级闭环：不接 Chroma、pgvector、真实法律库或生产级 citation 校验；mock fallback 必须保留。
