# 当前能力边界

本文说明 V1.0-alpha 当前已经完成和没有完成的内容，避免演示、交接和后续开发时把规划能力误认为已交付能力。

## 已完成

- WorkflowRuntime：统一管理 workflow start、review、resume、cancel 和运行状态。
- LangGraphAdapter：将 LangGraph StateGraph 收束为 Execution Adapter。
- NativeWorkflowAdapter：保留 Native YAML workflow 执行能力。
- `legal_contract_review_v1`：律师合同审查对外 canonical workflow id。
- aliases：兼容 `legal_contract_review_stategraph_v1` 和 `legal_contract_review_langgraph_v1`。
- LLM Gateway：统一模型调用入口。
- mock provider：测试和演示兜底。
- openai-compatible provider：兼容 OpenAI 风格接口的模型提供商。
- keyword Evidence Retriever：基于本地演示知识材料的关键词检索。
- Human Review：支持 approved、rejected、need_more_info 等审核决策。
- Trace：记录步骤执行、adapter 输出和治理事件。
- Report Markdown：审核通过后生成 Markdown 报告。
- AgentOS Console：查看 WorkflowRun、Trace、Review、Checkpoint 和运行状态。
- 律师合同审查工作台：业务入口，默认只展示“合同审查标准流程”。

## 未完成

- 完整法律法规库。
- 案例库。
- 向量检索。
- citation 版本校验。
- 文件上传解析到合同审查 workflow。
- 持久化 Checkpoint。
- Word / PDF 导出。
- 多职业工作流的完整生产闭环。
- 生产级权限策略。
- 生产级审计、租户隔离、数据脱敏和合规策略。

## 不能夸大的部分

当前 Evidence 是演示级本地知识库 + keyword 检索，不等同于正式法律依据库。它可以展示“证据对象如何进入工作流与报告”，但不能替代完整法律法规、司法解释、案例库和版本校验。

当前报告不是正式法律意见。报告只能作为合同审查辅助材料，必须由律师或合规负责人复核。

当前系统仍是 V1.0-alpha，不是 V1.0-beta，也不是生产可用的法律 RAG 平台。本阶段不接 Chroma、pgvector、FAISS，不接真实法律库，不扩展新功能。

## 当前可演示闭环

```text
合同文本
  -> legal_contract_review_v1
  -> LangGraphAdapter
  -> 风险识别
  -> keyword Evidence Retriever
  -> Human Review
  -> Report Markdown
  -> AgentOS Console 治理视图
```

## 当前稳定契约

workflow：

```text
id: legal_contract_review_v1
runtimeEngine: langgraph
implementationId: legal_contract_review_stategraph_v1
aliases:
  - legal_contract_review_stategraph_v1
  - legal_contract_review_langgraph_v1
```

artifacts：

```text
risks: output.artifacts.risk_detect.risks
evidences: output.artifacts.legal_evidence_match.evidences
report: output.artifacts.report_generate.report_markdown
```

review：

```text
approved       -> resume 到 report_generate，生成 report_markdown
rejected       -> 不生成 report_markdown
need_more_info -> 保持 waiting_review，不生成 report_markdown
```
