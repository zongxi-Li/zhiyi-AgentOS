# AgentOS 架构说明

# AgentOS Architecture Overview

本文描述 V1.0-alpha 当前真实架构。历史设计文档中出现的向量库、完整法律 RAG、pgvector、案例库、正式法律知识库等内容属于后续规划，不代表当前已经完成。

## 核心原则

AgentOS Core 是项目治理主线。它负责把专业任务纳入统一生命周期，而不是把某个执行框架当成系统内核。

核心能力包括：

- TaskManager：管理任务创建、推荐 workflow、任务状态。
- WorkflowRuntime：统一负责 start、resume、review、cancel 和运行状态推进。
- Trace：记录运行过程、步骤事件、adapter 输出和治理事件。
- Review：承载 Human Review 决策。
- Checkpoint：保存可恢复的运行状态快照。

这些能力组成 AgentOS 的治理边界。行业 workflow、模型调用、检索和 LangGraph 状态图都必须回写到同一套 `WorkflowRun`、Trace、Review、Checkpoint 和 artifacts 结构中。

## Execution Adapter

`WorkflowRuntime` 不直接绑定某个业务 workflow，也不把 LangGraph 放成平级内核。Runtime 根据 `WorkflowDefinition.runtimeEngine` 或 `executorType` 选择执行适配器。

当前保留两类 adapter：

- `NativeWorkflowAdapter`：执行 Native YAML workflow，适合稳定、线性、可配置的流程。
- `LangGraphAdapter`：执行 LangGraph StateGraph，当前承载律师合同审查实现。

当前合同审查的对外 workflow id 是：

```text
legal_contract_review_v1
```

当前内部实现是：

```text
runtimeEngine: langgraph
implementationId: legal_contract_review_stategraph_v1
```

兼容旧入口的 aliases：

```text
legal_contract_review_stategraph_v1
legal_contract_review_langgraph_v1
```

旧 id 只作为兼容入口存在，不再作为业务用户可见的 workflow 选择项。

## 前端双入口

前端保留两个入口，但不是两套内核：

- AgentOS Console：通用治理视图，展示 WorkflowRun、runtimeEngine、implementationId、run status、Trace、Checkpoint、Review。
- Legal Contract Workbench：律师合同审查工作台，面向业务演示，只展示“合同审查标准流程”。

两个入口共享同一套 `workflowApi` 和 `WorkflowRun` 数据结构。普通业务用户不需要知道 Native、LangGraph、StateGraph Runtime 或 AgentOS Native Migration 的差异。

## Legal Pack

Legal Pack 放行业相关内容，不进入 AgentOS Core：

- workflow definition
- prompt
- evidence schema
- report template
- 法律场景 agent / skill
- 本地演示知识材料

当前合同审查 workflow definition 位于：

```text
agent/packs/legal/workflows/contract_review.yaml
```

artifacts 契约保持稳定：

```text
risks: output.artifacts.risk_detect.risks
evidences: output.artifacts.legal_evidence_match.evidences
report: output.artifacts.report_generate.report_markdown
```

## 能力组件

LLM Gateway 与 Evidence Retriever 是能力组件，不是系统主干。

- LLM Gateway：统一封装 mock provider 和 openai-compatible provider，支持测试回退。
- Evidence Retriever：当前是演示级本地知识库 + keyword 检索，用于生成可展示 Evidence。

当前没有接入完整法律法规库、案例库、Chroma、pgvector、FAISS 或生产级 citation 校验。V1.0-alpha 的重点是演示 AgentOS 治理链路闭环。

## 当前运行链路

```text
用户在律师合同审查工作台输入合同
  -> Spring Boot Gateway
  -> Python AgentOS Core API
  -> TaskManager 创建任务
  -> WorkflowRuntime 启动 legal_contract_review_v1
  -> 根据 runtimeEngine 选择 LangGraphAdapter
  -> 执行 legal_contract_review_stategraph_v1
  -> 生成风险、Evidence、Trace
  -> Human Review
  -> approved 后生成 Report Markdown
  -> AgentOS Console 查看同一个 WorkflowRun
```

这条链路的展示重点是治理、可追踪、可审核和可交接，不是模型自由聊天。

## V1.0.6 Core 纯净化补充

V1.0.6 后，AgentOS Core 与应用层边界按以下规则冻结：

- `agentOS/src/agentos/core`、`domain`、`stores`、`workflow`、`execution` 不 import `app.*`、`app.graphs.*` 或 `langgraph`。
- `LangGraphAdapter` 位于 `agent/app/execution/`，不属于 Core。
- `LangGraphImplementationRegistry` 位于应用层，负责 `implementationId -> StateGraph Runtime` 映射。
- `legal_contract_review_stategraph_v1` 当前映射到 `agent/app/graphs/contract_review/runtime.py` 中的 `LegalContractReviewStateGraphRuntime`。
- `agent/app/graphs/legal_contract_review_stategraph.py` 只作为兼容 shim 保留。
- 合同审查 StateGraph 主体已经拆分到 `agent/app/graphs/contract_review/`。
- `contract_review/graph.py` 只负责图拓扑。
- `contract_review/nodes/*` 负责节点业务逻辑。
- `contract_review/projector.py` 负责 LangGraph State 到 AgentOS `WorkflowRun` 的投影。
- `contract_review/artifacts.py` 负责 artifact key 与稳定路径契约。
- Core 侧 `agentos.adapters.model_adapter` 只保留模型服务协议和注册入口；具体 `app.services.aiservice.AIService` 由 `agent/app/integrations/model_adapter.py` 在应用层注册。
