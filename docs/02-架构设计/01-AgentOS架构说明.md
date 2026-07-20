# AgentOS 架构说明

本文描述当前真实架构。历史设计文档中的完整法律知识库、生产级多租户、高可用 Workflow Store 等内容属于后续规划，不代表已经完成。

## 1. 核心原则

AgentOS Core 是项目治理主线，ACG 是动态群体智能的主要执行引擎。Core 不绑定具体行业流程，统一管理：

- TaskManager：任务创建、工作流推荐与任务状态。
- WorkflowRuntime：工作流启动、恢复、审核、取消和状态推进。
- Trace：步骤、模型调用、数据生产/消费和治理事件。
- Review：Human-in-the-loop 审核决策。
- Checkpoint：可恢复的步骤级运行快照。
- Evaluation：运行质量和治理指标。

行业 Workflow、模型调用和检索结果最终都写回统一的 `WorkflowRun`、Trace、Review、Checkpoint 和 artifacts 契约。

## 2. 执行路径

`WorkflowRuntime` 根据 `WorkflowDefinition.runtimeEngine` 选择 Core 内置执行路径：

- `native`：执行稳定的线性 YAML Workflow。
- `acg`：执行 ACG 就绪集调度，支持并行拓扑、低熵通信、Provenance、自愈和人审恢复。

两条路径复用同一套 `ExecutionAdapter` 协议和治理设施。标准合同审查只使用 ACG：

```text
workflowId: legal_contract_review_v1
runtimeEngine: acg
```

路由器只选择 `workflowId`，执行引擎由 Workflow 定义决定，不把引擎选择暴露给对话模型。

## 3. 前端入口

- AgentOS Console：通用治理视图，展示 WorkflowRun、运行状态、Trace、Checkpoint 和 Review。
- Legal Contract Workbench：面向合同审查的业务工作台。
- ACG Visualization：展示拓扑、数据血缘、低熵通信指标与恢复轨迹。

这些入口共享同一套 API 和 `WorkflowRun` 数据结构。

## 4. Legal Pack

法律业务实现位于 `agent/packs/legal/`，不进入 AgentOS Core：

- Workflow definition
- Agent / Skill
- Prompt 与 JSON Schema
- Evidence Retriever 与标准化结构
- 报告模板和本地 fallback

标准合同审查定义：

```text
agent/packs/legal/workflows/contract_review.yaml
```

稳定 artifacts 契约：

```text
risks:     output.artifacts.risk_detect.risks
evidences: output.artifacts.legal_evidence_match.evidences
report:    output.artifacts.report_generate.report_markdown
```

LLM 输出必须经过 JSON Schema 与业务校验；调用失败或结构非法时使用确定性 fallback。报告始终保留 Evidence 依据链、人工审核记录和法律免责声明。

## 5. 当前运行链路

```text
用户提交合同
  -> Spring Boot Gateway
  -> Python AgentOS Core API
  -> TaskManager 创建任务
  -> WorkflowRuntime 启动 legal_contract_review_v1
  -> ACGWorkflowAdapter / ACGExecutor
  -> parse_contract -> classify_clauses -> risk_detect
  -> legal_evidence_match -> suggestion_generate
  -> human_review（暂停并创建 Checkpoint）
  -> approved 后恢复 report_generate
  -> WorkflowRun 输出 Report / Trace / Provenance / Metrics
```

## 6. Core 边界

- `agentOS/src/agentos/core` 不 import `app.*` 或行业 Pack。
- Core 只提供通用模型、协议、状态机、执行、规划和治理能力。
- 应用层在 `agent/app/execution/runtime.py` 注入 Intent LLM 和实例锁。
- 法律、教育等领域能力通过 Pack Registry 注册。
- 模型服务具体实现由 `agent/app/integrations/model_adapter.py` 注入，Core 只保留协议。

当前系统仍以可演示、可追踪、可审核的闭环为重点；正式法律知识库、生产级 citation 校验与高可用存储仍需继续工程化。
