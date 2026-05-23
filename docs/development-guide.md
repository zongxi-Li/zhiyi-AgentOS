# 开发指南

本文说明当前项目的开发、启动、测试和提交约束。

## 模块职责

- `backend/`：Spring Boot 后端，使用 Maven 管理，负责认证、业务 API、AgentOS Gateway 和 Java 侧测试。
- `frontend/`：Vue 3 前端，使用 npm 管理，负责 AgentOS Console、律师合同审查工作台和其他用户界面。
- `agent/`：Python FastAPI 应用层，使用 pytest 验证，负责 AgentOS Core API 入口、Legal Pack、LLM Gateway、Evidence Retriever 等能力组件。
- `agentOS/`：AgentOS Core 源码，承载 TaskManager、WorkflowRuntime、Trace、Review、Checkpoint、Execution Adapter 等核心能力。
- `docker-compose.yml`：整体开发环境编排，包含 postgres、redis、ai-service、backend、frontend。

## 日常启动建议

日常开发推荐分模块启动，这样定位问题更快。

基础依赖：

```bash
docker compose up -d postgres redis
```

Python Agent：

```bash
cd agent
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Spring Boot 后端：

```bash
cd backend
mvn spring-boot:run
```

Vue 前端：

```bash
cd frontend
npm install
npm run dev
```

默认地址：

```text
Frontend: http://localhost:3000
Backend : http://localhost:8080
Agent   : http://localhost:8000
```

## Docker Compose

Docker Compose 负责整体服务编排，适合集成演示或验证服务组合。

Windows：

```powershell
.\dev.ps1 up
```

Linux/macOS：

```bash
./dev.sh up
```

直接使用 Docker Compose：

```bash
docker compose up -d --build
```

只检查配置：

```bash
docker compose config
```

不要把 Docker Compose 和 Maven / npm / pytest 理解为替代关系：

- Maven 验证 Spring Boot 后端。
- npm 验证 Vue 前端。
- pytest 验证 Python Agent 与 AgentOS Core。
- Docker Compose 验证整体服务编排。

## 测试要求

提交前必须运行：

```bash
cd agent
python -m pytest tests
```

```bash
cd frontend
npm run build
```

```bash
cd backend
mvn test
```

如果改动涉及 Docker 配置，再运行：

```bash
docker compose config
```

## 提交前检查

不要提交：

- `.env`
- API Key
- `dist/`
- `target/`
- `__pycache__/`
- `.pytest_cache/`
- 日志文件
- 真实合同文本
- 真实客户、案件、当事人数据

可以提交：

- `.env.example`
- 文档
- 测试代码
- mock 数据
- 脱敏演示样例

## V1.0-alpha 约束

当前阶段只冻结演示链路和项目说明，不进入 V1.0-beta。

本阶段不要做：

- 接 Chroma / pgvector / FAISS。
- 接真实法律库或案例库。
- 重构 AgentOS Core 架构。
- 恢复旧 V0.7 合同审查专用 API。
- 让业务用户选择 Native / LangGraph runtime。
- 把 LangGraph 表述为 AgentOS Core 本身。
