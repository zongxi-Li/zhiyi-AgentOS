# 知弈 Agent 结构

---

## 1. 总体结构

```text
agent/
	app/
		main.py
			FastAPI 应用入口，统一注册 Core API、RAG、聊天和行业包路由。

		config.py
			运行配置入口，统一读取模型、跨域、路径、超时等环境变量。

		api/
			agentos_core.py
				AgentOS Core API，负责任务创建、工作流启动、状态查询、审核和恢复。

			chat.py
				普通聊天入口，适合轻任务；复杂任务可升级为 WorkflowRun。

			rag.py
				RAG 查询入口，提供文档检索和知识增强能力。

		core/
			orchestration/
				types.py
					定义 AgentTask、WorkflowDefinition、WorkflowRun、WorkflowStep、Checkpoint、TraceEvent、ReviewDecision。

				workflow_runtime.py
					管理 WorkflowRun 生命周期，负责启动、推进、暂停、取消和查询。

				orchestrator.py
					核心编排器，负责选择下一步、调度 Agent、处理失败、触发审核、汇总结果。

				workflow_registry.py
					加载和注册所有行业工作流模板。

				state_machine.py
					统一管理任务、工作流、步骤和 Agent 的状态迁移。

				checkpoint.py
					创建、查询和恢复 Checkpoint，支持长任务续跑。

				trace.py
					记录执行轨迹，保存任务、步骤、Agent、工具和错误事件。

				review.py
					处理人工审核节点，支持通过、驳回、重跑和终止。

				evaluation.py
					计算工作流级指标，例如完成率、恢复率、循环率和协作质量。

			agents/
				base.py
					定义 BaseAgent 和统一 Agent 接口。

				registry.py
					注册和发现所有行业 Agent。

				packs/
					legal/
						manifest.yaml
							声明法律包元信息、版本、可用 Agent 和 Workflow。

						workflows/
							contract_review.yaml
								合同审查工作流定义，描述每一步由哪个 Agent 执行。

							case_analysis.yaml
								案件分析工作流定义。

						agents/
							case_intake.py
								案情接收 Agent。

							statute.py
								法条检索 Agent。

							evidence.py
								证据分析 Agent。

							risk.py
								风险评估 Agent。

							draft.py
								文书草拟 Agent。

							review.py
								审查 Agent。

						skills/
							legal_search.py
								法律检索工具。

							legal_reason.py
								法律推理工具。

						prompts/
							case_intake.md
								案情接收提示词模板。

							risk_assess.md
								风险评估提示词模板。

					education/
						manifest.yaml
							教育包元信息和注册声明。

						workflows/
						agents/
						skills/
						prompts/

					finance/
						manifest.yaml
							金融包元信息和注册声明。

						workflows/
						agents/
						skills/
						prompts/

					medical/
						manifest.yaml
							医疗包元信息和注册声明。

						workflows/
						agents/
						skills/
						prompts/

					government/
						manifest.yaml
							政务包元信息和注册声明。

						workflows/
						agents/
						skills/
						prompts/

			memory/
				session_memory.py
					短期会话记忆。

				workflow_memory.py
					工作流中间产物和步骤上下文。

				profile_memory.py
					用户偏好和组织配置。

				career_memory.py
					职业经验、模板和规则。

				federated_memory.py
					匿名联邦经验统计。

			react/
				planner.py
					步骤内部局部规划器。

				executor.py
					步骤内部执行器。

				tool_router.py
					工具路由器，把动作映射到 Skill。

			schema/
				agent_types.py
					旧 DTO 兼容层，后续迁移到 orchestration/types.py。

			skills/
				base.py
					Skill 基类，统一输入输出约束。

				...
					各专业领域 Skill 原子，由 Agent 调用，不由 Orchestrator 直接调用。

			retrieval/
				chroma_client.py
					向量数据库客户端。

				...
					各行业索引构建器。

			federated/
				federated_adapter.py
					联邦增强适配器，后续接入推荐、调度和偏好学习。

		ai_engine/
			deepseekadapter.py
				DeepSeek 文本生成适配器。

			qwenadapter.py
				通义千问适配器。

			speechadapter.py
				语音能力适配器。

			multimodaladapter.py
				多模态能力适配器。

			kylin_sdk/
				麒麟生态 SDK 封装。

			harmony_sdk/
				鸿蒙生态 SDK 封装。

		services/
			aiservice.py
				统一 AI 服务封装。

			ragservice.py
				RAG 服务封装。

			performancemonitor.py
				性能监控与指标采集。

			federatedlearning.py
				联邦学习与经验统计服务。
```

---

## 2. 设计原则

```text
Core 只管运行时。
Pack 负责行业能力。
Workflow 由配置定义。
Agent 由类实现。
Skill 由工具实现。
Orchestrator 只调度，不硬编码业务。
```

---

## 3. 最终分工

| 层级 | 负责什么 | 是否硬编码行业逻辑 |
|---|---|---|
| `Core` | 调度、状态、恢复、审计、评估 | 否 |
| `Pack` | 行业 Agent、Workflow、Skill、Prompt、规则 | 否，按包插件化注册 |
| `Agent` | 专业任务执行 | 否，依赖包注入 |
| `Skill` | 具体能力原子 | 可以代码实现，但不写死到 Core |
| `Workflow` | 步骤流转 | 否，配置化 |
| `Registry` | 发现和加载 | 否，通用机制 |

---

## 4. 最终判断

这套结构的目标不是“把所有东西塞进一个大目录”，而是：

```text
让知弈成为可扩展的 AgentOS 底座，
让行业能力通过 Pack 进入系统，
让 Core 永远保持通用、稳定、可治理。
```
