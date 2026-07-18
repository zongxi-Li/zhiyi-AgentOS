# 知弈 AgentOS 文档索引

本目录按 **为什么做 → 做成什么 → 怎么实现 → 如何演示** 的阅读顺序组织。建议新成员从 `01` 开始顺序通读。

## 01-赛题与项目概述

项目的出发点：赛题背景、系统定位、技术路线与竞品对比。

| 文档 | 说明 |
| --- | --- |
| [01-项目设计方案](01-赛题与项目概述/01-项目设计方案.md) | 项目背景、问题定义、总体目标与核心设计思想 |
| [02-技术选型与技术路线报告](01-赛题与项目概述/02-技术选型与技术路线报告.md) | 现状分析、技术栈选型与演进路线 |
| [03-同类竞品分析对比](01-赛题与项目概述/03-同类竞品分析对比.md) | 与 LangGraph、AutoGen 等竞品的分层对比 |
| 04-知弈AgentOS路线和赛题对接.docx | 赛题能力维度对接说明（交付物） |

## 02-架构设计

系统做成了什么：整体架构、代码层次与各引擎技术设计。

| 文档 | 说明 |
| --- | --- |
| [01-agentos-architecture](02-架构设计/01-agentos-architecture.md) | AgentOS 总体架构说明 |
| [02-core-arch](02-架构设计/02-core-arch.md) | Core / Java / 前端代码层次架构 |
| [03-agent-structure](02-架构设计/03-agent-structure.md) | 知弈 Agent 应用层结构 |
| [04-agentos-v1.0.6-boundary](02-架构设计/04-agentos-v1.0.6-boundary.md) | V1.0.6 边界与稳定契约 |
| [05-acg-engine-technical-design](02-架构设计/05-acg-engine-technical-design.md) | ACG 动态群体智能引擎技术设计 |
| [06-lawyer-agentos-technical-design](02-架构设计/06-lawyer-agentos-technical-design.md) | 律师 AgentOS 技术设计文档 |
| [figures/](02-架构设计/figures/) | 架构 drawio 源图 |

## 03-开发记录

怎么一步步实现：能力边界、待办与历次实现计划。

| 文档 | 说明 |
| --- | --- |
| [02-core-todo](03-开发记录/02-core-todo.md) | Core TODO 与进度摘要 |
| [03-2026-05-15-console-governance-plan](03-开发记录/03-2026-05-15-console-governance-plan.md) | Console 与治理实现计划 |
| [04-2026-05-22-domain-models](03-开发记录/04-2026-05-22-domain-models.md) | 领域模型实现计划 |
| [05-2026-07-18-docker-p0-p1-implementation](03-开发记录/05-2026-07-18-docker-p0-p1-implementation.md) | Docker P0/P1 基础设施实施记录 |
| [06-2026-07-18-p1-windows-docker-desktop](03-开发记录/06-2026-07-18-p1-windows-docker-desktop.md) | Windows Docker Desktop 开发环境记录 |

## 04-演示与交付

如何对外展示：演示流程、测试样例与最终报告。

| 文档 | 说明 |
| --- | --- |
| [02-acg-test-samples](04-演示与交付/02-acg-test-samples.md) | ACG 可视化面板功能测试样例集 |
| [03-acg-engine-final-report](04-演示与交付/03-acg-engine-final-report.md) | ACG 引擎最终技术报告 |
| [figures/](04-演示与交付/figures/) | 演示相关图示 |

## 05-设计资料归档

早期设计材料与原始内容提取稿，仅用于追溯设计演进，不作为当前能力说明。

| 文档 | 说明 |
| --- | --- |
| [01-初步设计提取稿](05-设计资料归档/01-初步设计提取稿.md) | 从早期设计文档整理出的 Markdown 原始提取稿 |
