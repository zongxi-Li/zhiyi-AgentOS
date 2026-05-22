# 知弈 AgentOS 开源参考调研

日期：2026-05-22

这份文档只看官方仓库和官方文档，目标不是找一个“能整包替换”的项目，而是把你的系统拆成几条能力链，分别找最值得借的开源代码。

## 先说结论

对知弈来说，最值得参考的不是单一平台，而是五类开源组合：

1. Agent 运行时和治理：状态机、HITL、trace、checkpoint、handoff、sandbox。
2. RAG 和文档管线：解析、切块、索引、引用、图检索、评估。
3. 语音和数字人：ASR、TTS、克隆音色、口型驱动。
4. 联邦学习和隐私计算：训练、调度、可视化、远程数据使用。
5. 行业 Pack：法律、教育、编程、写作的任务模板和工作流。

你的项目最该学的，不是 UI 皮肤，而是“可注册、可追踪、可恢复、可审核”的工程骨架。

## 1. Agent 运行时和治理

- [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph)：适合看长期运行的状态图、持久化执行、人类接管、恢复机制，最贴近 `agentOS/src/agentos/core`。
- [microsoft/agent-framework](https://github.com/microsoft/agent-framework)：适合看 Python/.NET 双栈、多 Agent 编排、生产化部署和样板项目。
- [openai/openai-agents-python](https://github.com/openai/openai-agents-python)：适合看最小可用的 agent / handoff / guardrails / tracing / sessions 接口设计。
- [agno-agi/agno](https://github.com/agno-agi/agno)：适合看一个完整 Agent 平台如何把存储、审批、观测、RBAC、调度做成产品能力。
- [All-Hands-AI/OpenHands](https://github.com/All-Hands-AI/OpenHands)：适合看 SDK、CLI、本地 GUI、沙盒执行、评测体系怎么拆层。
- [SWE-agent/SWE-agent](https://github.com/SWE-agent/SWE-agent)：适合看任务驱动、YAML 化配置、工具调用循环和 trajectory 记录。
- [Aider-AI/aider](https://github.com/Aider-AI/aider)：适合看最小化的 git-aware 编码代理工作流。

## 2. 控制台和工作流 UI

- [langgenius/dify](https://github.com/langgenius/dify)：适合看产品化的 Agent / Workflow / RAG / observability 组合方式。
- [FlowiseAI/Flowise](https://github.com/FlowiseAI/Flowise)：适合看可视化节点编排、调试、评估和 HITL 的交互方式。
- [coze-dev/coze-studio](https://github.com/coze-dev/coze-studio)：适合看 agent、workflow、plugin、knowledge base、API/SDK 一体化的产品层。
- [labring/FastGPT](https://github.com/labring/FastGPT)：适合看知识库、流程编排和企业私有部署的交互模型。
- [agno-agi/agent-ui](https://github.com/agno-agi/agent-ui)：适合看现代 agent 聊天界面和运行态展示方式。

## 3. RAG 和文档管线

- [infiniflow/ragflow](https://github.com/infiniflow/ragflow)：适合看高质量文档理解、引用、模板化 RAG 和可编排的 ingestion 流程。
- [deepset-ai/haystack](https://github.com/deepset-ai/haystack)：适合看 retrieval / routing / memory / generation 的模块化管线。
- [run-llama/llama_index](https://github.com/run-llama/llama_index)：适合看文档代理、OCR、索引抽象和工具生态。
- [microsoft/graphrag](https://github.com/microsoft/graphrag)：适合看从非结构化文本里抽结构化实体/关系，再做图检索的套路。
- [HKUDS/LightRAG](https://github.com/HKUDS/LightRAG)：适合看轻量图 + 向量混合检索、评估和追踪接入。
- [docling-project/docling](https://github.com/docling-project/docling)：适合看多格式文档解析、局部执行、MCP 接口和多种导出格式。
- [opendatalab/MinerU](https://github.com/opendatalab/MinerU)：适合看复杂版式 PDF / Office 转 Markdown/JSON 的高精度管线。
- [Unstructured-IO/unstructured](https://github.com/Unstructured-IO/unstructured)：适合看通用文档 ETL、partition、chunk 和 embedding 流程。
- [neo4j/neo4j-graphrag-python](https://github.com/neo4j/neo4j-graphrag-python)：适合看 Neo4j 图数据库上的 GraphRAG 实现。

## 4. 语音和数字人

- [modelscope/FunASR](https://github.com/modelscope/FunASR)：适合看 ASR、VAD、标点恢复、说话人相关能力和实时识别。
- [FunAudioLLM/CosyVoice](https://github.com/FunAudioLLM/CosyVoice)：适合看多语种 TTS、音色克隆和部署栈。
- [myshell-ai/OpenVoice](https://github.com/myshell-ai/OpenVoice)：适合看零样本音色克隆和风格控制。
- [TMElyralab/MuseTalk](https://github.com/TMElyralab/MuseTalk)：适合看实时口型驱动和数字人视频生成。
- [OpenTalker/SadTalker](https://github.com/OpenTalker/SadTalker)：适合看音频驱动的人脸动画。
- [dsd2077/CyberVerse](https://github.com/dsd2077/CyberVerse)：适合看一个端到端数字人 Agent 平台怎么把 avatar、LLM、TTS、ASR、视频通话串起来。

## 5. 联邦学习和隐私计算

- [adap/flower](https://github.com/adap/flower)：适合看框架无关的联邦学习抽象、策略和训练样板。
- [FedML-AI/FedML](https://github.com/FedML-AI/FedML)：适合看分布式训练、模型服务、联邦学习和调度一体化。
- [FederatedAI/FATE](https://github.com/FederatedAI/FATE)：适合看工业级联邦学习、MPC/HE、集群部署和治理。
- [OpenMined/PySyft](https://github.com/OpenMined/PySyft)：适合看“数据不出域”的远程数据科学和权限策略。
- [FederatedAI/FATE-Board](https://github.com/FederatedAI/FATE-Board)：适合看联邦任务可视化、日志和运行监控面板。

## 6. 行业 Pack 和模板系统

- [accordproject/template-engine](https://github.com/accordproject/template-engine) 和 [accordproject/template-studio](https://github.com/accordproject/template-studio)：适合看法律模板、条款拼装、模板编辑器和机器可读合同。
- [neo4j-product-examples/graphrag-contract-review](https://github.com/neo4j-product-examples/graphrag-contract-review)：适合看合同审查里的 GraphRAG + 查询检索 + Q&A 流程。
- [deacs11/CrewAI_Contract_Clause_Risk_Assessment](https://github.com/deacs11/CrewAI_Contract_Clause_Risk_Assessment)：适合看多 Agent 合作做合同风险识别和审查摘要。
- [hasnaintypes/lawbotics](https://github.com/hasnaintypes/lawbotics)：适合看法律文档抽取、条款识别和合同分析的产品形态。
- [THU-MAIC/OpenMAIC](https://github.com/THU-MAIC/OpenMAIC)：适合看多 Agent 教室、课件、测验、白板和 TTS 的教学工作流。
- [CaviraOSS/PageLM](https://github.com/CaviraOSS/PageLM)：适合看 NotebookLM 风格的学习材料转化、卡片和播客输出。
- [HKUDS/DeepTutor](https://github.com/HKUDS/DeepTutor)：适合看持久化、多实例、CLI-first 的个性化辅导 Agent。
- [raestrada/storycraftr](https://github.com/raestrada/storycraftr)：适合看写作大纲、章节和故事世界构建的工作流。

## 7. 直接映射到你的仓库

- `agentOS/src/agentos/core`：优先对标 LangGraph、Agent Framework、OpenAI Agents SDK、Agno。
- `agent/packs/*`：优先对标 Accord Project、OpenMAIC、PageLM、DeepTutor、StoryCraftr。
- `agent/app/services/rag*` 和 `agent/app/data/*`：优先对标 RAGFlow、Docling、MinerU、Haystack、LightRAG。
- `agent/app/ai_engine/*` 和 `agent/app/services/*voice*`：优先对标 FunASR、CosyVoice、OpenVoice、MuseTalk。
- `frontend/src/components/agentos`：优先对标 Dify、Flowise、Coze Studio、OpenHands、Agno 的运行态和控制台思路。
- `agent/app/services/federated*`：优先对标 Flower、FedML、FATE、PySyft。

## 8. 最值得先读的组合

1. 先读 `langchain-ai/langgraph`、`microsoft/agent-framework`、`openai/openai-agents-python`、`agno-agi/agno`。
2. 再读 `infiniflow/ragflow`、`docling-project/docling`、`opendatalab/MinerU`、`deepset-ai/haystack`。
3. 编程代理看 `All-Hands-AI/OpenHands`、`SWE-agent/SWE-agent`、`Aider-AI/aider`。
4. 语音和数字人看 `modelscope/FunASR`、`FunAudioLLM/CosyVoice`、`myshell-ai/OpenVoice`、`TMElyralab/MuseTalk`。
5. 联邦学习看 `adap/flower`、`FedML-AI/FedML`、`FederatedAI/FATE`、`OpenMined/PySyft`。
6. 行业模板看 `accordproject/template-engine`、`THU-MAIC/OpenMAIC`、`HKUDS/DeepTutor`、`raestrada/storycraftr`。

## 9. 许可证提醒

- `Dify`、`FastGPT`、`MinerU` 这类项目都要先看仓库 LICENSE，不要默认等于纯 MIT/Apache。
- `OpenHands` 的核心是 MIT，但企业目录不是同一层级的开放方式。
- `template-studio` 是归档仓库，适合读思路，不适合当长期依赖。
- `Accord Project`、`Flowise`、`Coze Studio`、`LangGraph`、`OpenAI Agents SDK`、`Flower`、`FedML`、`FATE`、`PySyft` 这些更适合做长期工程参考，但也要以仓库 LICENSE 为准。

## 10. 最终判断

如果你要把知弈做成“职业智能体操作系统”，最靠谱的路径不是照搬某一个大平台，而是：

- 用 `LangGraph` / `Agent Framework` / `OpenAI Agents SDK` / `Agno` 定义运行时骨架。
- 用 `RAGFlow` / `Docling` / `MinerU` / `Haystack` 定义知识与文档链路。
- 用 `OpenHands` / `SWE-agent` / `Aider` 定义程序员 Pack。
- 用 `FunASR` / `CosyVoice` / `OpenVoice` / `MuseTalk` 定义语音和数字人。
- 用 `Flower` / `FedML` / `FATE` / `PySyft` 定义联邦和隐私增强。
- 用 `Accord Project` / `OpenMAIC` / `PageLM` / `DeepTutor` / `StoryCraftr` 定义行业 Pack。

这条路线更像一个真正的 AgentOS，而不是把几个模型 API 拼起来。
