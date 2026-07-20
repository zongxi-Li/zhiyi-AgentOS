# AgentOS V1.0.6 边界说明

本文记录当前代码边界，用于后续版本校准架构口径。

## 1. Core 边界

`agentOS/src/agentos/` 是 AgentOS Core 与通用框架层，负责：

- Task / WorkflowRun 生命周期。
- TraceStore、CheckpointStore、ReviewManager 和 Evaluation。
- WorkflowRegistry、TaskManager、Orchestrator 和状态机。
- Native 与 ACG 执行适配协议。
- 通用模型服务协议和注册入口。

Core 不应直接依赖：

- `app.*`
- `app.services.*`
- 法律、教育等具体 Pack
- 具体业务 Workflow

## 2. ACG 执行边界

ACG 是 Core Native 自研执行引擎，主要组件位于：

```text
agentOS/src/agentos/core/acg/
agentOS/src/agentos/core/execution/acg_executor.py
agentOS/src/agentos/core/planning/
agentOS/src/agentos/core/communication/
```

职责划分：

- ACG Blueprint 描述 Step、Control、Memory 和依赖/通信边。
- ACGExecutor 根据就绪集调度节点并复用 Orchestrator 分派 Agent。
- ContextAssembler 按 `input.fields` 精准投递上游数据。
- ProvenanceLedger 记录数据生产与消费血缘。
- Review、Checkpoint、Trace 和 Evaluation 继续由 Core 统一治理。

## 3. 合同审查业务边界

标准合同审查位于法律 Pack：

```text
agent/packs/legal/workflows/contract_review.yaml
agent/packs/legal/agents/contract_review_migration.py
agent/app/llm/prompts/contract_review_prompts.py
agent/app/rag/
```

公开契约：

```text
workflowId: legal_contract_review_v1
runtimeEngine: acg

risks:     output.artifacts.risk_detect.risks
evidences: output.artifacts.legal_evidence_match.evidences
report:    output.artifacts.report_generate.report_markdown
```

Human Review 行为：

```text
approved       -> 恢复 report_generate 并完成报告
rejected       -> WorkflowRun failed
need_more_info -> 保持 waiting_review
cancelled      -> WorkflowRun cancelled
```

## 4. 应用层注入边界

`agent/app/execution/runtime.py` 只负责应用运行时配置：

- 注入真实 Intent LLM Gateway。
- 获取 Workflow Store 实例锁。
- 构建默认 WorkflowRuntime。

`agent/app/integrations/model_adapter.py` 注册具体模型服务。Pack 可以使用 Core 暴露的模型协议，但 Core 不反向 import 应用服务。

## 5. 当前演示链路

```text
律师合同审查工作台
  -> Spring Boot Gateway
  -> Python AgentOS Core API
  -> WorkflowRuntime
  -> ACGExecutor
  -> Legal Pack agents
  -> Human Review / Checkpoint
  -> Report / Trace / Provenance / Metrics
```

当前法律检索和 fallback 仍以演示闭环为主，正式法规库、案例库、生产级 citation 校验和高可用 Workflow Store 属于后续工程化范围。
