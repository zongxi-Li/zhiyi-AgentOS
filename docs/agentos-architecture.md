# AgentOS Core 主线与执行适配器

## V1.0.2 收束原则

AgentOS Core 是项目的治理主线。TaskManager、WorkflowRuntime、Trace、Review、Checkpoint 和 Evaluation 构成稳定的任务生命周期与审计边界。

LangGraph 不是 AgentOS Core 本身，而是 Execution Adapter。它用于承载复杂状态图、人工中断、恢复和分支执行，但运行结果必须回写为同一套 WorkflowRun、Trace、Review、Checkpoint 和 artifacts 结构。

Native YAML workflow 也是 Execution Adapter。稳定、线性的行业流程可以继续通过 YAML steps 与 Orchestrator 执行。

## 前端入口

前端保留两个入口：

- AgentOS Console：通用治理视图，用于查看 WorkflowRun、Engine、Implementation、Trace、Checkpoint、Review 和运行状态。
- Legal Contract Workbench：法律行业工作台，用于启动合同审查、查看风险、证据、报告和人工审核。

两个入口共享同一套 workflowApi 和 WorkflowRun 数据结构，不恢复旧 V0.7 合同审查专用 API。

## 合同审查 Workflow ID

对外 canonical workflow id：

```text
legal_contract_review_v1
```

当前内部实现：

```text
runtimeEngine: langgraph
implementationId: legal_contract_review_stategraph_v1
```

兼容旧入口的 aliases：

```text
legal_contract_review_stategraph_v1
legal_contract_review_langgraph_v1
```

业务用户只看到“合同审查标准流程”。具体 Native/LangGraph 实现属于开发者信息，不作为普通业务选择项暴露。

## Artifacts 契约

合同审查 artifacts 路径保持兼容：

```text
risks: output.artifacts.risk_detect.risks
evidences: output.artifacts.legal_evidence_match.evidences
report: output.artifacts.report_generate.report_markdown
```
