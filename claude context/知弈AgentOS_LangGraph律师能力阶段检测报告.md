# 知弈 AgentOS LangGraph 律师能力阶段检测报告

生成日期：2026-06-10

## 1. 当前结论

**合同审查 StateGraph 模块化拆分阶段**，主要依据是合同审查流程已拆分到 `agent/app/graphs/contract_review/`，`graph.py` 只负责 StateGraph 拓扑，`state.py`、`runtime.py`、`projector.py`、`artifacts.py` 与 `nodes/` 分工清晰，旧 `legal_contract_review_stategraph.py` 仅作为兼容导出；同时 canonical workflow 已通过 `runtimeEngine=langgraph` 和 `implementationId=legal_contract_review_stategraph_v1` 接入 Core Adapter。

但当前能力仍应定位为 **可运行的 demo 闭环 / mock-driven 工程验证版**，不是 V1.0-beta 或生产级律师合同审查能力。主要原因是 LLM 默认 mock，部分节点仍是固定规则输出，本地法律知识库明确标注为演示资料，RAG 只是本地关键词检索加 fallback。

本轮已执行的验证命令：

| 命令                                                                                                                                                                    | 结果      | 说明                                                                                                                                      |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `rg --files` 与多组 `rg -n` 关键词搜索                                                                                                                              | 通过      | 已定位 LangGraph、Core、Adapter、LLM Gateway、RAG、Artifact、Trace、Review、前后端链路                                                    |
| `python -m pytest -q agent/tests/test_legal_contract_review_stategraph.py agent/tests/test_lawyer_contract_review_migration.py`                                       | 14 passed | 覆盖 StateGraph 启动、waiting_review、approved resume、rejected、need_more_info、RAG fallback、API start/review/trace/checkpoints/metrics |
| `python -m pytest -q agentOS/tests/test_task_manager.py agentOS/tests/test_task_manager_events.py agentOS/tests/test_progress.py agentOS/tests/test_domain_models.py` | 18 passed | 覆盖 Core TaskManager、Runtime 状态流转、progress、领域模型                                                                               |
| `npm run build`                                                                                                                                                       | 通过      | 前端可构建；存在 Sass legacy API 和 chunk size warning                                                                                    |
| `mvn -q -Dtest=AgentOsGatewayControllerTest test`                                                                                                                     | 通过      | Java 网关能转发 AgentOS Core workflow、trace、checkpoint、review、metrics API                                                             |

## 2. 已实现能力清单

| 能力                                 | 状态     | 证据文件                                                                                                                  | 说明                                                                                                                                                                                      |
| ------------------------------------ | -------- | ------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| StateGraph 构建                      | 已实现   | `agent/app/graphs/contract_review/graph.py`                                                                             | 注册 `parse_contract -> classify_clauses -> risk_detect -> legal_evidence_match -> suggestion_generate -> human_review -> report_generate`，并 `interrupt_before=["report_generate"]` |
| StateGraph 模块化拆分                | 已实现   | `agent/app/graphs/contract_review/*`                                                                                    | `state.py`、`graph.py`、`runtime.py`、`projector.py`、`artifacts.py`、`nodes/` 职责明确                                                                                       |
| 旧 StateGraph 兼容导出               | 已实现   | `agent/app/graphs/legal_contract_review_stategraph.py`                                                                  | 旧文件仅导出新包对象，并保留兼容 monkeypatch 入口                                                                                                                                         |
| canonical workflow id                | 已实现   | `agent/packs/legal/workflows/contract_review.yaml`                                                                      | `legal_contract_review_v1` 指向 `runtimeEngine: langgraph` 与 `implementationId: legal_contract_review_stategraph_v1`                                                               |
| Core / Adapter 解耦                  | 已实现   | `agentOS/src/agentos/core/runtime.py`, `agent/app/execution/runtime.py`, `agent/app/execution/langgraph_adapter.py` | Core 通过 ExecutionAdapterFactory 调用，app 层注册 `langgraph` adapter                                                                                                                  |
| LangGraph implementation registry    | 已实现   | `agent/app/execution/langgraph_registry.py`                                                                             | `legal_contract_review_stategraph_v1` 映射到 `LegalContractReviewStateGraphRuntime`                                                                                                   |
| Workflow 从合同文本跑到人工审核      | 已实现   | `agent/tests/test_legal_contract_review_stategraph.py`                                                                  | start 后自动跑到 `human_review: waiting_review`，`report_generate` 保持 pending                                                                                                       |
| Human Review approve 后继续生成报告  | 已实现   | `agent/app/graphs/contract_review/runtime.py`, `report_generate.py`                                                   | `APPROVED` 通过 LangGraph `Command(update=...)` 继续到 report                                                                                                                         |
| Human Review reject / need_more_info | 部分实现 | `agent/app/graphs/contract_review/runtime.py`                                                                           | `rejected` 置 failed；`need_more_info` 保持 waiting_review；`cancelled/rerun/request_changes` 未完整支持                                                                            |
| Checkpoint                           | 部分实现 | `agentOS/src/agentos/core/governance/checkpoint.py`, `projector.py`                                                   | 每个 completed/waiting_review step 会写入 run 内 checkpoint；默认内存，配置 SQLite 时随 run payload 持久化；没有独立 checkpoint 表                                                        |
| LangGraph checkpoint / thread 绑定   | 已实现   | `graph.py`, `runtime.py`                                                                                              | `InMemorySaver` + `thread_id = run.run_id`，人工审核 approve 用同一 run_id 恢复                                                                                                       |
| 通用 checkpoint resume               | 部分实现 | `agentOS/src/agentos/core/runtime.py`                                                                                   | `/resume` 走 Core native `_run_until_blocked`，未按 runtime engine 委派给 LangGraph Adapter                                                                                           |
| LLM Gateway                          | 已实现   | `agent/app/llm/gateway.py`, `providers/*`                                                                             | 支持 mock 与 openai-compatible，配置缺失或失败 fallback mock                                                                                                                              |
| 节点接入 LLM Gateway                 | 部分实现 | `parse_contract.py`, `risk_detect.py`, `report_generate.py`                                                         | 三个节点走 Gateway；`classify_clauses` 和 `suggestion_generate` 仍是固定规则/样例输出                                                                                                 |
| 本地法律知识库                       | 部分实现 | `agent/knowledge/legal/*`                                                                                               | 有 Markdown/JSON 演示资料，内容明确标注不是正式法规库                                                                                                                                     |
| Keyword RAG                          | 部分实现 | `agent/app/rag/legal_retriever.py`, `providers/keyword_retriever.py`                                                  | `legal_evidence_match` 可真实检索本地 chunk；无向量检索、无正式法规校验                                                                                                                 |
| Evidence Schema                      | 部分实现 | `agent/app/rag/legal_evidence_schema.py`                                                                                | 有 `id/riskId/sourceType/sourceName/title/content/citationText/chunkId/confidence/retrievalScore/metadata`                                                                              |
| Risk 与 Evidence 绑定                | 部分实现 | `legal_evidence_match.py`, `risk_detect.py`                                                                           | Evidence 有 `riskId`；risk 的 `evidenceIds` 未在 RAG 后回填真实 evidence id                                                                                                           |
| Artifact 路径契约                    | 已实现   | `agent/app/graphs/contract_review/artifacts.py`, `frontend/src/utils/agentos/contractReviewArtifactExtractor.ts`      | 关键路径为 `output.artifacts.risk_detect.risks`、`output.artifacts.legal_evidence_match.evidences`、`output.artifacts.report_generate.report_markdown`                              |
| Trace                                | 部分实现 | `agentOS/src/agentos/core/governance/trace.py`, `projector.py`, `nodes/common.py`                                   | 能记录 task/run/node/review/completed；节点没有统一 step_started/success/error、durationMs 多为 0                                                                                         |
| Python FastAPI Core API              | 已实现   | `agent/app/api/agentos_core.py`, `agent/app/main.py`                                                                  | 暴露 `/ai/core/tasks`、`/ai/core/workflows/start`、runs、trace、checkpoints、reviews、resume、cancel、metrics                                                                         |
| Java Spring Boot Gateway             | 已实现   | `backend/src/main/java/com/kinlin/ai/controller/AgentOsGatewayController.java`                                          | `/api/agentos`、`/agentos`、`/ai` 转发到 Python `/ai/core/*`                                                                                                                      |
| 前端律师工作台                       | 已实现   | `frontend/src/views/LawyerContractReviewWorkbenchView.vue`                                                              | 合同审查模板为 backend 模式，调用真实 workflow API，展示 risk/evidence/report/trace/checkpoint/review                                                                                     |

## 3. 当前 LangGraph 合同审查链路图

真实代码链路如下：

```text
START
  ↓
parse_contract
  ↓
classify_clauses
  ↓
risk_detect
  ↓
legal_evidence_match
  ↓
suggestion_generate
  ↓
human_review
  ↓
[interrupt_before report_generate]
  ↓ approved review via WorkflowRuntime.apply_review()
report_generate
  ↓
END
```

实际运行行为：

| 节点                     | 输入 state                                  | 输出 state / artifact                                               | LLM | RAG                   | mock/fallback                                            | trace                                                      | 异常处理                      |
| ------------------------ | ------------------------------------------- | ------------------------------------------------------------------- | --- | --------------------- | -------------------------------------------------------- | ---------------------------------------------------------- | ----------------------------- |
| `parse_contract`       | `contract_text`                           | `artifacts.parse_contract`                                        | 是  | 否                    | LLM 失败或 JSON 不合规时 `_mock_parse_contract_output` | `agent_called` + LLM payload                             | Gateway helper 捕获           |
| `classify_clauses`     | 当前 state，实际主要固定输出                | `artifacts.classify_clauses`                                      | 否  | 否                    | 固定样例分类                                             | `agent_called`                                           | 无显式异常处理                |
| `risk_detect`          | `contract_text` + artifacts               | `state.risks`, `artifacts.risk_detect`                          | 是  | 否                    | `_risk_items()`                                        | `agent_called` + LLM payload                             | Gateway helper 捕获           |
| `legal_evidence_match` | `risks`, `parse_contract.contract_type` | `state.evidences`, `artifacts.legal_evidence_match`             | 否  | 是，keyword retriever | 检索无结果或异常时 mock evidence                         | `agent_called` + `retriever_type/top_k/fallback/error` | try/except                    |
| `suggestion_generate`  | `risks`                                   | `artifacts.suggestion_generate`，同时改写 `risk_detect.risks`   | 否  | 否                    | 固定 riskId 映射                                         | `agent_called`                                           | 无显式异常处理                |
| `human_review`         | suggestions / risks                         | `status=waiting_review`, `artifacts.human_review`               | 否  | 否                    | demo reviewer                                            | `review_required`                                        | 无显式异常处理                |
| `report_generate`      | approved `review`, risks, evidences       | `status=completed`, `artifacts.report_generate.report_markdown` | 是  | 使用已有 evidences    | LLM 失败时模板报告；未 approve 则 failed                 | `agent_called` 或 `step_failed`                        | approve gate + Gateway helper |

## 4. 当前核心问题

### P0：必须立即解决，否则链路不可用

当前没有发现阻断 demo 链路运行的 P0。合同文本可以通过 Core Runtime + LangGraph Adapter 自动跑到 `waiting_review`，审核通过后可以生成报告。

### P1：影响 V1.0-beta 质量

| 问题描述                                                                | 影响                                                                                                                                               | 涉及文件                                                                                                              | 建议修复方式                                                                                                                                 |
| ----------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| RAG 仍是演示知识库 + 关键词检索，法律资料明确标注为演示，不是正式法规库 | 不能宣称真实法律依据匹配完成；报告中的依据只能作为演示线索                                                                                         | `agent/knowledge/legal/*`, `agent/app/rag/*`, `legal_evidence_match.py`                                         | 冻结 Evidence Schema；接入经过校验的法规/规则数据源；检索不命中时明确返回“无依据”而不是自动 mock                                           |
| risk 与 evidence 只做单向关联                                           | Evidence 有 `riskId`，但 risk 的 `evidenceIds` 未回填真实 evidence id，前后链路难以审计 claim-to-evidence                                      | `risk_detect.py`, `legal_evidence_match.py`, `suggestion_generate.py`                                           | 在 `legal_evidence_match` 后按 `riskId` 回填 `risk.evidenceIds`，报告必须引用这些 ID                                                   |
| `classify_clauses`、`suggestion_generate` 仍是固定样例逻辑          | 对非软件开发合同或 LLM 生成的新 risk id 适配差，律师能力容易退化成 demo                                                                            | `classify_clauses.py`, `suggestion_generate.py`                                                                   | 引入结构化 schema 和 Gateway/RAG 约束；至少按 risk 内容生成建议，不依赖固定 risk id                                                          |
| 通用 `/resume` 未对 LangGraph workflow 委派 Adapter                   | 前端 checkpoint resume 入口存在，但 Core `resume_from_checkpoint()` 会走 native `_run_until_blocked`，对 LangGraph run 不是真正恢复 StateGraph | `agentOS/src/agentos/core/runtime.py`, `agent/app/execution/langgraph_adapter.py`, `contract_review/runtime.py` | 给 ExecutionAdapter 增加 `resume_from_checkpoint`，Core resume 按 `runtimeEngine` 委派；LangGraph runtime 用 thread_id/checkpointer 恢复 |
| Trace 不足以完整审计每个节点                                            | 缺 step start/success/error 的统一事件，durationMs 多为 0，输入/输出摘要不稳定                                                                     | `nodes/common.py`, `projector.py`, `trace.py`                                                                   | 封装节点执行 wrapper，统一写 `step_started`、`agent_called/success`、`step_failed`、duration、input/output summary                     |
| Human Review 决策枚举与产品语义不完全一致                               | 代码支持 `approved/rejected/need_more_info`，但 `request_changes/rerun/cancelled` 没有在 LangGraph runtime 中完整落地                          | `runtime.py`, `HumanReviewPanel.vue`, `types.py`                                                                | 明确审核语义：`need_more_info` 是否等价 request_changes；补 `rerun/cancelled` 或在 UI/API 中隐藏不可用状态                               |

### P2：后续优化

| 问题描述                                    | 影响                                                                        | 涉及文件                                                              | 建议修复方式                                                     |
| ------------------------------------------- | --------------------------------------------------------------------------- | --------------------------------------------------------------------- | ---------------------------------------------------------------- |
| Checkpoint 缺独立持久化模型                 | 默认内存；SQLite 时随 run payload 保存，缺 checkpoint 单独查询/生命周期管理 | `checkpoint.py`, `sqlite_workflow_store.py`                       | 需要生产化时拆出 checkpoint 表与 state blob 版本                 |
| Artifact schema 分散在节点内                | 前端依赖关键路径，但节点输出字段缺集中契约测试                              | `artifacts.py`, `nodes/*`, `contractReviewArtifactExtractor.ts` | 增加 `ContractReviewArtifacts` schema 与契约测试               |
| openai-compatible provider 仅基础 JSON 模式 | 不含重试、结构化修复、成本/超时指标细分                                     | `gateway.py`, `openai_compatible_provider.py`                     | 加 provider-level retry、JSON repair、metrics、fallback reason   |
| 前端仍有部分非合同模板走 preview            | 不影响合同审查，但容易让用户混淆“真实后端能力”和“前端预览”              | `agentWorkbench.ts`, `LawyerContractReviewWorkbenchView.vue`      | 在模板配置中明确 runtime 状态，演示时只强调合同审查 backend 链路 |

## 5. 关键技术缺口逐项判断

### 5.1 Workflow 是否真实可运行

| 问题                                           | 判断                                                                    |
| ---------------------------------------------- | ----------------------------------------------------------------------- |
| 是否能从初始合同文本跑到 `report_generate`？ | 能，但必须先到 `human_review` 中断，审核 approved 后继续              |
| 是否需要手动调用 step？                        | 不需要逐步手动调用；`start()` 自动跑到中断点                          |
| 是否支持自动执行？                             | 支持，直到 `interrupt_before report_generate`                         |
| 是否支持 interrupt？                           | 支持，使用 LangGraph `interrupt_before=["report_generate"]`           |
| interrupt 后是否能 resume？                    | 人审 approved 路径能 resume；通用 checkpoint resume 对 LangGraph 不完整 |
| thread_id / run_id 是否正确绑定？              | LangGraph config 使用 `thread_id=run.run_id`                          |

### 5.2 Human Review 是否真实有效

| 问题                                        | 判断                                                                 |
| ------------------------------------------- | -------------------------------------------------------------------- |
| 是否真的在 `report_generate` 前中断？     | 是，start 后 `report_generate` pending，run 为 `waiting_review`  |
| 是否有 `waiting_review` 状态？            | 是，run/task/step 都可进入 `waiting_review`                        |
| 是否能 approve / reject / request_changes？ | approve、reject、need_more_info 可用；request_changes 未作为独立枚举 |
| approve 后是否能继续生成报告？              | 是，测试已覆盖 completed 与 report artifact                          |
| trace 中是否记录人审事件？                  | 是，`review_required` 与 `review_decided` 均会记录               |

### 5.3 RAG 是否只是样子

| 问题                                         | 判断                                                                                                                                         |
| -------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| `legal_evidence_match` 是否真实检索？      | 是，本地 Markdown/JSON 资料会被 loader/splitter/keyword retriever 检索                                                                       |
| 检索结果是否参与 `report_generate`？       | 是，report prompt 和 fallback 报告都引用 `state.evidences`                                                                                 |
| risk 与 evidence 是否有关联 ID？             | 部分。Evidence 有 `riskId`，但 risk 的 `evidenceIds` 未回填                                                                              |
| evidence 是否有 source、title、text、score？ | 部分。字段为 `sourceType/sourceName/title/content/citationText/retrievalScore/confidence`                                                  |
| 是否存在模型直接生成法律依据而非 RAG 返回？  | 合同节点 prompt 禁止编造依据；报告生成要求引用 `state.evidences`。但默认 mock 报告和 fallback 仍可能给出模板化“依据链”，必须保持演示标识 |

### 5.4 Artifact 是否足够稳定

| 问题                           | 判断                                                  |
| ------------------------------ | ----------------------------------------------------- |
| 每个节点输出是否结构化？       | 是，大多为 dict/list；报告主内容为 Markdown string    |
| artifact 字段是否固定？        | 关键路径固定；完整节点 schema 仍分散                  |
| 前端是否依赖这些字段？         | 是，前端 extractor 依赖 risk/evidence/report 三条路径 |
| 是否有自由文本导致后续难解析？ | report_markdown 是自由 Markdown；其它节点较结构化     |

### 5.5 Trace 是否足够审计

| 问题                              | 判断                                                                                      |
| --------------------------------- | ----------------------------------------------------------------------------------------- |
| trace 是否记录每个节点？          | 基本记录，每个节点 append trace                                                           |
| 是否记录状态变化？                | task 状态变化有记录；LangGraph 节点 step 状态变化主要反映在 run.steps，不一定有独立 trace |
| 是否记录错误？                    | LLM 错误进入 payload 的 mock_fallback；真正 step failed 记录有限                          |
| 是否记录耗时？                    | LLM latency 在 payload；TraceEvent.durationMs 多数为 0                                    |
| 是否能从 trace 复盘一次合同审查？ | 可以粗略复盘，尚不足以做严格审计                                                          |

### 5.6 前后端是否真正联通

| 问题                                       | 判断                                                                                |
| ------------------------------------------ | ----------------------------------------------------------------------------------- |
| 前端看到的是 mock 还是真实 Agent Runtime？ | 合同审查模板调用真实 `workflowApi`；但结果内容可能来自 mock/default demo provider |
| Spring Boot 是否只是内存状态机？           | 不是。Java 网关主要转发到 Python AgentOS Core，本身不维护 workflow 状态             |
| Python FastAPI 是否被调用？                | 是，Java 转发 `/ai/core/*`；前端 dev/proxy 也以 `/ai` 为 baseURL                |
| report 是否来自 LangGraph 结果？           | 是，来自 `output.artifacts.report_generate.report_markdown`                       |
| 人审操作是否能传回 Python Runtime？        | 是，前端 `submitReview()` 调 `/core/workflows/runs/{runId}/reviews`             |

## 6. 下一步设计计划

### 阶段 A：律师 LangGraph 链路打通

目标：确保合同文本可以稳定跑完整 LangGraph 链路。

输出：

| 输出物                      | 验收标准                                                                  |
| --------------------------- | ------------------------------------------------------------------------- |
| 完整 artifacts              | 每个节点都有固定 schema 与契约测试                                        |
| 完整 trace                  | 每个节点有 start/success/error/duration/input summary/output summary      |
| 可恢复 human_review         | approved/rejected/need_more_info/request_changes/rerun/cancelled 语义清楚 |
| 最终 report                 | 只在 approved 后生成，并引用 risk/evidence ID                             |
| LangGraph checkpoint resume | `/resume` 对 langgraph workflow 不再走 native runtime                   |

### 阶段 B：律师能力增强

目标：提升合同解析、风险识别、证据匹配、建议生成的专业稳定性。

重点：

| 重点                 | 设计方向                                                                              |
| -------------------- | ------------------------------------------------------------------------------------- |
| Risk Schema          | 冻结 `id/title/level/clause/reason/consequence/suggestion/evidenceIds/confidence`   |
| Evidence Schema      | 保留 `riskId`，增加 `claimId/sourceAuthority/sourceVersion/validity` 等可审计字段 |
| RAG 约束             | 不命中返回空 evidence + 明确提示；禁止自动 mock 成正式依据                            |
| 报告结构             | 报告按 risk id 组织，每条建议必须绑定 evidence 或标注“无正式依据”                   |
| LLM Gateway fallback | fallback 只产出“待人工补充”的保守结果，不产出伪依据                                 |

### 阶段 C：前后端联调与演示闭环

目标：前端律师工作台可以展示真实 LangGraph 结果。

重点：

| 重点              | 设计方向                                                         |
| ----------------- | ---------------------------------------------------------------- |
| Task 状态         | 展示 created/running/waiting_review/completed/failed             |
| Step 状态         | 每个节点展示输入摘要、输出摘要、耗时、错误                       |
| Trace 面板        | 支持按 run/step/event 过滤，区分 LLM/RAG/Human events            |
| Evidence 面板     | 展示 riskId、sourceName、citationText、score、demo/official 标识 |
| Human Review 操作 | UI 只展示后端支持的决策；补 request_changes 语义                 |
| Report 面板       | 报告引用 evidence id，可追溯到检索来源                           |

## 7. 建议的下一轮 Codex 实现任务

任务 1：冻结 `ContractReviewState / Risk / Evidence / Artifact` Schema

涉及文件：

```text
agent/app/graphs/contract_review/state.py
agent/app/rag/legal_evidence_schema.py
agent/app/graphs/contract_review/artifacts.py
agent/tests/test_legal_contract_review_stategraph.py
frontend/src/utils/agentos/contractReviewArtifactExtractor.ts
```

验收标准：

```text
1. risk、evidence、report artifact 字段集中定义。
2. Python 和前端 extractor 的关键字段一致。
3. 测试覆盖 output.artifacts.risk_detect / legal_evidence_match / report_generate。
```

任务 2：打通 full `run_contract_review()` 契约测试

涉及文件：

```text
agent/app/graphs/contract_review/runtime.py
agent/app/graphs/contract_review/projector.py
agent/tests/test_legal_contract_review_stategraph.py
```

验收标准：

```text
1. 从合同文本 start 后自动进入 waiting_review。
2. approved 后 completed，并生成 report_markdown。
3. rejected / need_more_info 不生成 report。
4. trace、checkpoint、artifacts 均可 API 查询。
```

任务 3：完善 LangGraph human_review resume 与 checkpoint resume

涉及文件：

```text
agentOS/src/agentos/core/execution/adapters.py
agentOS/src/agentos/core/runtime.py
agent/app/execution/langgraph_adapter.py
agent/app/graphs/contract_review/runtime.py
frontend/src/components/agentos/CheckpointPanel.vue
```

验收标准：

```text
1. WorkflowRuntime.resume_from_checkpoint() 按 runtimeEngine 委派 adapter。
2. LangGraph run 的 checkpoint resume 不再走 native _run_until_blocked。
3. approved / rejected / need_more_info / cancelled 的行为有明确测试。
```

任务 4：让 RAG 结果回填 risk.evidenceIds

涉及文件：

```text
agent/app/graphs/contract_review/nodes/legal_evidence_match.py
agent/app/graphs/contract_review/nodes/suggestion_generate.py
agent/app/graphs/contract_review/nodes/report_generate.py
agent/tests/test_legal_contract_review_stategraph.py
```

验收标准：

```text
1. 每个 risk.evidenceIds 对应真实 evidence.id。
2. report 中每个风险项能展示 evidence id 或明确“无正式依据”。
3. RAG 无命中时不把 mock evidence 伪装成正式法律依据。
```

任务 5：统一节点 Trace wrapper

涉及文件：

```text
agent/app/graphs/contract_review/nodes/common.py
agent/app/graphs/contract_review/nodes/*.py
agent/app/graphs/contract_review/projector.py
agentOS/src/agentos/core/governance/trace.py
```

验收标准：

```text
1. 每个节点都有 step_started、agent_called 或 step_succeeded、step_failed。
2. trace 有 durationMs、inputSummary、outputSummary、error。
3. 前端 Trace 面板可看到节点级耗时和失败原因。
```

## 8. 不建议现在做的事情

| 不建议事项                | 原因                                                                  |
| ------------------------- | --------------------------------------------------------------------- |
| 大规模 benchmark          | 当前更缺 schema、resume、RAG 约束和审计链路，benchmark 会掩盖工程缺口 |
| 多模型横向对比            | LLM Gateway 已有抽象，但核心律师链路仍需先稳定                        |
| 新增太多职业角色          | 合同审查样板还未达到可治理闭环质量，扩角色会稀释主线                  |
| 做复杂 UI 动效            | 前端已能展示核心面板，优先补真实数据质量与 trace                      |
| 接入真实商用法律数据库    | 先把 Evidence Schema、no-hit 策略、引用审计做好，再接正式数据源       |
| 把律师能力写成单一 prompt | 当前架构目标是 Workflow + RAG + Review + Trace，不应退化成聊天 prompt |

## 9. 建议执行的测试命令

下一轮实现后建议至少执行：

```bash
python -m pytest -q agent/tests/test_legal_contract_review_stategraph.py agent/tests/test_lawyer_contract_review_migration.py
python -m pytest -q agentOS/tests/test_task_manager.py agentOS/tests/test_task_manager_events.py agentOS/tests/test_progress.py agentOS/tests/test_domain_models.py
npm run build
mvn -q -Dtest=AgentOsGatewayControllerTest test
```

如果本轮后续要扩大验证面，再执行：

```bash
python -m pytest -q agent/tests agentOS/tests
mvn test
```
