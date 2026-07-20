# 知弈 AgentOS Docker 基础设施 P2 实施报告

实施日期：2026-07-19（Asia/Shanghai）

结论：P2 的代码开发、Docker Desktop 联调和自动化验收已经完成；安全链路、普通代理、SSE、Trace ID 和结构化日志均有实际测试证据。2026-07-19 最终门禁闭环已完成，状态更新为 `P2_ACCEPTED_WINDOWS`。该状态只代表 Windows 11 + Docker Desktop 开发环境验收通过；`P1.5-Linux` 仍为 `BLOCKED_EXTERNAL_ENVIRONMENT`，不得据此宣称 Linux、麒麟或生产发布验收通过。

## 1. Git 基线与保护点

- 分支：`master`
- 起始工作区：`git status --short` 为空，退出码 0。
- P2 起始 HEAD：`2398305cd6b6476ac8ca16e751257f2ceec02264`
- 保护分支：`backup/pre-p2-2398305c`
- 稳定标签：`p2-start-2398305c`
- 未执行 `reset`、`checkout`、历史重写或强制推送。
- 最新前端基线提交为 `2398305 feat: 优化对话栏的输入效果`；P2 保留其页面布局、模型设置和客户端 URL，仅调整请求安全边界、SSE 取消能力及开发代理方向。

任务开始时执行并通过：

```powershell
git status --short
git branch --show-current
git rev-parse HEAD
git log -10 --oneline
```

## 2. P2.0 现状审计

### 原始调用路径

- 普通聊天：Frontend `/api/chat/text` → Java `ChatController/AiService` → Python `/ai/chat/text`。
- AgentOS：Frontend `/ai/core/**` → Java `AgentOsGatewayController/AgentOsGatewayService` → Python `/ai/core/**`。
- SSE：Frontend `fetch + ReadableStream` → Nginx/Vite → Java/Python；生产 Nginx 已指向 Java，但旧 Nginx 和 Vite 开发代理仍存在直连 Python配置。
- 前端按 `data:` 行解析 JSON 增量，以 `[DONE]` 结束；没有稳定的 AbortController 生命周期和心跳处理。

### 审计发现

1. Java 曾对 `/ai/core/**` 匿名放行，部分用户上下文从客户端 `X-User-Id` 或默认 UUID 取得。
2. Java 到 Python 存在 WebClient 和 RestTemplate 等多处调用，内部令牌、用户头和 Trace 注入未统一。
3. Python 可以读取内部令牌配置，但业务路由没有统一强制验证。
4. 普通代理部分上游错误被包装为 HTTP 200，错误体可能暴露上游路径或异常细节。
5. Java SSE 的 240 秒是总时长、可能丢弃心跳，客户端取消没有完整传播；Python 未稳定检查断开。
6. Trace ID、MDC/ContextVar 和生产 JSON 日志未形成全链路。
7. 最新前端提交主要改变聊天输入与页面交互；P2 采用最小兼容改造，没有重做页面。

最小方案为：保留外部 URL，以 Java 为唯一 AI 安全边界；统一 Python Client 注入服务令牌和可信用户上下文；普通和 SSE 走同一认证链；Nginx/Vite 均只指向 Java；增加 Trace/日志而不改变业务数据架构。

## 3. 实际修改文件

### Frontend

- `frontend/src/services/api/agentos.ts`
- `frontend/src/services/api/conversation.ts`
- `frontend/src/stores/chat.ts`
- `frontend/src/utils/request.ts`
- `frontend/vite.config.ts`
- `frontend/Dockerfile.dev`

### Nginx

- `frontend/nginx-main.conf`
- `frontend/nginx.conf`
- `docker/nginx/default.conf`
- `docker/nginx/nginx.conf`

### Backend

- 配置/过滤器：`FilterConfig`、`InterceptorConfig`、`SecurityConfig`、`WebClientConfig`、`WebConfig`、`JwtAuthenticationFilter`、`SensitiveIdentityHeaderFilter`、`TraceIdFilter`、`RequestLoggingFilter`。
- 网关：`AiGatewayHeaders`、`AiInternalServiceToken`、`PythonServiceAuthentication`、`TrustedUserContextForwarder`、`AiProxyService`、`AiSseGatewayService`。
- 控制器/服务：`AiServiceProxyController`、`AgentOsGatewayService`、`AgentGatewayService`、`GlobalExceptionHandler`。
- 身份/日志：`AuthenticatedUserContext`、`TraceContext`、`LogRedactor`、两个 Logback 脱敏 Converter、`logback-spring.xml`。
- 配置：`application.yml`、`application-prod.yml`、`pom.xml`。

### FastAPI / AgentOS

- `agent/app/security/internal_auth.py`
- `agent/app/middleware/trace.py`
- `agent/app/observability/context.py`
- `agent/app/utils/logger.py`
- `agent/app/api/chat.py`
- `agent/app/api/agentos_core.py`
- `agent/app/api/sse_test.py`（仅 `SSE_TEST_MODE=true` 注册）
- `agent/app/main.py`、`config.py`、`middleware/errorhandler.py`
- 模型客户端日志脱敏修订。
- 未引入 PostgreSQL Workflow Store；SQLite 仍为单实例、单 Worker。

### Docker / Compose

- `.env.windows.example`：增加非敏感 SSE 配置示例。
- `compose.dev.yaml`：增加 test profile、心跳、空闲/最大时长的非敏感传递。
- `compose.yaml`、`compose.prod.yaml`、卷名、网络拓扑、Flyway 迁移和备份恢复脚本均未改变。

### Tests

- Python：`test_internal_service_auth.py`、`test_sse_streaming.py`、`test_trace_and_logging.py`、`test_gateway_test_provider.py`。
- Java：身份头过滤、内部认证、可信用户、普通代理、SSE、Trace、日志脱敏和 JWT 测试。

## 4. 安全设计

- 所有 `/ai/**` 在 Java 要求合法 JWT；匿名请求实测为 401。
- Java 从 `Authentication` 构造 `AuthenticatedUserContext`，不从客户端身份头生成身份。
- `SensitiveIdentityHeaderFilter` 删除 `X-User-Id`、角色/租户/组织/工作台头、可信用户头和客户端内部令牌。
- Java 到 Python 统一使用 `X-Internal-Service-Token`；令牌从 configtree Secret 读取，空值、短值和占位值失败。
- Python 启动时从 `AI_INTERNAL_TOKEN_FILE` 读取一次，使用常量时间比较；缺失 401，错误/空值/重复头 403。
- Python 健康端点例外，业务端点同时要求内部令牌和完整可信用户上下文。
- Java 只转发受控请求头，不转发 Cookie、客户端 Authorization 或身份/内部认证头；目标基址固定，不能由客户端选择，避免 SSRF。
- RestTemplate 内部认证最终限定到 `AgentGatewayService` 的 Python 客户端，避免污染 Spring `TestRestTemplate` 或其他本地客户端。

实际 HTTP 证据：

```text
unauth_ai_status=401
proxy_upstream_200=200
proxy_upstream_400=400
proxy_upstream_401=401
proxy_upstream_403=403
proxy_upstream_404=404
proxy_upstream_409=409
proxy_upstream_422=422
proxy_upstream_500=502
trusted_user_matches_jwt=True
forged_role_rejected=True
expired_or_invalid_jwt_status=401
direct Python business endpoint=401
direct Python health endpoint=200
```

## 5. 普通代理

链路固定为：Client → Frontend/Vite 或 Nginx → Spring Boot → FastAPI。

- Nginx `/ai/**` 和 Vite `/ai/**` 只到 Backend。
- 方法、路径、请求体和 Content-Type 保持；上游 URL 固定为配置的 Python 服务。
- 2xx 和安全 4xx 保持状态；上游 500 映射为 502 `AI_UPSTREAM_ERROR`，私有错误细节不透传。
- 连接失败映射为 503 `AI_UPSTREAM_UNAVAILABLE`；连接超时/读取超时在 Java 单元测试中映射为稳定错误码。
- 所有安全错误体带 `traceId`，不以 HTTP 200 包装失败。

首次执行全量 Maven 时，3 个原有集成测试失败：全局 RestTemplate Customizer 错误地对请求 Java 本机的 `TestRestTemplate` 强制读取内部令牌。修复为仅在 `AgentGatewayService` 构建的 Python RestTemplate 上注入后，`129/129` 通过。

## 6. SSE 网关

- 事件仍使用 `text/event-stream`、`data:`、空行分隔和 `[DONE]`；前端不会显示 `:` 注释心跳。
- Python 默认心跳间隔 15 秒；Java 和 Nginx 不缓冲、不吞心跳。
- `SSE_IDLE_TIMEOUT=240000ms` 是空闲超时，事件或心跳重置计时。
- `SSE_MAX_DURATION=1800000ms` 是可配置总时长上限。
- 客户端关闭 → Java Reactor 取消上游 → Python `request.is_disconnected()`/取消异常 → 任务状态清理。
- 测试 Provider 只在 `SSE_TEST_MODE=true` 注册；验收后恢复 false，并通过 OpenAPI 确认 `/ai/test/sse` 和 `/ai/test/proxy/**` 不存在。

容器证据：

```text
短时正常流：HTTP 200，首包约 629ms，[DONE]=true
默认心跳：15 秒间隔通过
缩短空闲超时：3 秒，SSE_IDLE_TIMEOUT
缩短最大时长：12 秒，SSE_MAX_DURATION
客户端取消：Python state=cancelled
Java：SSE downstream cancelled; upstream subscription cancelled
生产 Nginx 长流：267.4 秒，49 个心跳，[DONE]=true
生产 Nginx 首心跳：5570ms（该长流验收使用 5 秒测试心跳）
```

真实超过 240 秒的测试使用临时生产 Nginx 容器，仅连接 ingress/web 网络；完成后已删除临时容器，没有把 Docker Desktop 结果描述为 Linux 生产验收。

## 7. Trace ID 与日志

- Nginx 接受合法 UUID/32 hex，否则用受控 `$request_id`；隐藏上游重复头并只返回一次。
- Java 再次验证/生成，写 MDC，响应及 Python 请求使用同一值，finally 清理线程上下文。
- Python ASGI Middleware 用 ContextVar 覆盖整个请求和 SSE 生成器生命周期；Workflow/Task 日志补充对应 ID。
- 实测合法 Trace 在 Nginx → Java → Python → 响应完全一致；非法和超长值被替换；16 路并发单元测试无串号。
- Java `json-logs` 与 Python production JSON 固定字段为：`timestamp`、`level`、`service`、`trace_id`、`workflow_id`、`task_id`、`message`、`exception`；可附加 HTTP 字段。
- Nginx JSON access log包含 trace、方法、路径、状态和时长。
- Authorization、Cookie、JWT、内部令牌、模型 Key、数据库/Redis密码和 Secret 正文不记录。

机器校验：Python 生产 JSON 2 行全部能由 `ConvertFrom-Json` 解析且固定字段齐全。最终运行态扫描：

```text
runtime_known_secret_hits=0
runtime_jwt_hits=0
runtime_model_key_hits=0
p2_added_known_secret_hits=0
p2_added_jwt_hits=0
p2_added_model_key_hits=0
```

## 8. Docker Desktop 验收

环境边界：Windows 11 专业版 10.0.26100（64 位）、Docker Desktop `desktop-linux` context、Docker Client/Engine 29.0.1、Linux amd64 Engine、Compose 2.40.3-desktop.1。它只构成 Windows 开发验收。

标准组合：

```powershell
docker compose `
  -f compose.yaml `
  -f compose.dev.yaml `
  -f compose.windows.yaml `
  --env-file .env.windows `
  up -d --build
```

构建时 Frontend `npm ci` 和 FastAPI `pip install` 层均为 `CACHED`；Backend 因 `pom.xml` 增加日志依赖重新解析依赖，后续源码挂载不需要重建依赖层。

最终五服务均 healthy：

```text
frontend  healthy  127.0.0.1:18088->8080/tcp
backend   healthy  8080/tcp, 5005/tcp（未发布）
ai-service healthy 8000/tcp（未发布）
postgres  healthy  5432/tcp（未发布）
redis     healthy  6379/tcp（未发布）
```

连接矩阵实测：

| 来源 | Backend | FastAPI | PostgreSQL | Redis | 外部 HTTPS |
| --- | --- | --- | --- | --- | --- |
| Frontend | 200 | BLOCKED | BLOCKED | BLOCKED | 未要求 |
| Backend | — | CONNECTED | CONNECTED | CONNECTED | 可能具备出站能力 |
| FastAPI | ConnectionRefused | — | BLOCKED | BLOCKED | 200 |

Backend 只监听 web-network 地址 `192.168.48.2:8080`，因此 FastAPI 即使与 Backend 同处 agent-network，也不能反向连接 Backend 的 agent-network 地址。agent-network 允许外部出站，因此 Backend 和 FastAPI 均可能具备出站能力；本阶段只保证入站和横向访问隔离，不实现域名级出站控制。

宿主机端口：18088 LISTENING；18080、18000、5432、6379 均 BLOCKED。Frontend inspect 最终只有 `127.0.0.1:18088`。

## 9. 数据、迁移和备份回归

- P2 未修改 `compose.yaml`、`compose.prod.yaml`、Flyway SQL、`baselineOnMigrate=false`、`ddl-auto=validate`、卷名、备份/恢复脚本或 RFC v1.1。
- Schema 实际审计：`state=managed`，SHA-256 指纹长度 64，错误列表为空。
- PostgreSQL 重启前后用户计数均为 26。
- 新建 AgentOS 任务 `task_0458bc91a183`，重启 FastAPI 后 SQLite 查询匹配数为 1。
- 上传文件 `p2-acceptance/84ecec77-befd-457e-a6d0-9b397b7e2b5d.txt`，重启 Backend 后仍存在。
- SQLite 在线备份 `integrity_check=ok`，备份中任务数为 4；临时备份随后删除。
- Redis 维护窗口式 `SAVE` 返回 OK，`rdb_last_bgsave_status=ok`，DBSIZE=0。当前 Redis 为可重建缓存，恢复失败不应覆盖关键状态恢复结论。
- 基础设施备份/恢复/Schema/防火墙/Windows 脚本自动化共 20 项通过；P2 没有对其实现文件产生差异。

## 10. 测试命令与结果

| 命令 | 退出码 | 结果 |
| --- | ---: | --- |
| `python -m pytest -q agent/tests` | 0 | 134 passed, 1 skipped, 214 warnings |
| `mvn -f backend/pom.xml test` | 0 | 129 tests, 0 failures, 0 errors |
| `npm run build` | 0 | vue-tsc + Vite，3469 modules transformed |
| `python -m pytest -q scripts/infra/tests` | 0 | 20 passed |
| Windows Compose `config --quiet` | 0 | PASS |
| Prod Compose `config --quiet` | 0 | PASS（仅静态渲染） |
| Dev Compose `config --quiet` | 0 | PASS |
| Observability 组合 `config --quiet` | 0 | PASS |
| canonical/legacy Nginx `nginx -t` | 0 | 三种配置分别 PASS |
| Frontend production image build | 0 | PASS，只有 Sass/大 chunk 警告 |

测试警告主要是 Pydantic class Config、Python 3.14 asyncio 和 Sass legacy API 弃用警告；没有测试失败被忽略。

## 11. Git 提交

| Commit | Message | 对应验收 |
| --- | --- | --- |
| `011c93a` | `feat(ai-security): 建立 Java 与 Python 内部服务认证` | 内部令牌正/负向、健康例外 |
| `c2b9480` | `fix(auth-gateway): 统一 AI 请求身份与可信用户上下文` | JWT、伪造头、可信用户 |
| `cc55249` | `feat(ai-proxy): 统一普通 AI 请求网关和错误传播` | 路由、状态码、错误映射 |
| `ca89fa4` | `feat(sse-gateway): 实现 Java SSE 心跳超时与取消传播` | 心跳、idle/max、长流、取消 |
| `49dc899` | `feat(observability): 增加 Trace ID 和结构化日志` | Trace、JSON日志、脱敏 |
| `5378dfc` | `fix(ai-security): 限定内部令牌注入到 Python 客户端` | 修复全量集成测试发现的注入越界 |
| `60a5a0d` | `test(ai-gateway): 完成 AI 网关端到端安全验收` | 确定性 Provider、容器状态码与身份验收 |

## 12. 未解决问题与门禁

1. 大前端 bundle 和依赖弃用警告不阻断 P2，但应在独立性能/升级任务处理。
2. P1.5-Linux 缺少目标麒麟/Linux 主机、SSH、真实网关来源和防火墙探测端，状态保持 `BLOCKED_EXTERNAL_ENVIRONMENT`。
3. Docker Desktop 结果不是 rootful Linux Secret 权限、Linux 防火墙、麒麟、ARM 或正式私有化发布验收。

## 13. 下一步判定

当前判定：`P2_ACCEPTED_WINDOWS`。P2 代码级功能、安全、Windows 容器联调和最终工作树门禁均已通过。

该判定不解锁 Linux、麒麟或生产发布验收。进入相关阶段前仍需获得目标麒麟/rootful Linux 环境，并完成延期的 P1.5 入口、Secret 权限、网络边界和防火墙验收。

## 14. 最终门禁闭环

闭环日期：2026-07-19（Asia/Shanghai）。

### 14.1 工作区归属与 Chroma 测试隔离

- `frontend/src/utils/request.ts` 与 `frontend/src/views/ChatView.vue` 已由用户独立处理；本次闭环未修改、恢复或重新提交这两个文件。闭环开始时 `git status --short` 和 `git diff --stat` 均为空。
- tracked 文件 `agent/app/data/legal_chroma/chroma.sqlite3` 的基线 SHA-256 为 `5EB1A9E3C95075971A524FEF4D95CE08B68914272AAB2F6E34654D9EC54B3031`。修复前运行 `python -m pytest -q agent/tests` 后变为 `544DF0EE1A52EB2DAE9947FAB8C97D8E2584AD7B82E99EE666798CEE3CE2CD15`，证明测试副作用可稳定复现。
- 根因是 `agentos.adapters.retrieval.chroma_client` 在测试模块导入阶段创建全局 `PersistentClient`，默认打开仓库中的 tracked 数据库。
- `agent/tests/conftest.py` 现于测试收集前将 `AGENT_CHROMA_PATH` 指向独立临时目录；会话结束先调用 Chroma 公开的 `client.close()` 释放 Windows SQLite 文件锁，再清理临时目录。生产默认路径和运行时代码未改变。
- 隔离后全量 Agent 测试为 `134 passed, 1 skipped`，数据库前后 SHA-256 均保持 `5EB1A9E3C95075971A524FEF4D95CE08B68914272AAB2F6E34654D9EC54B3031`，且 `git status --short` 不再出现该文件。
- 隔离修复已作为独立提交 `8285fe5 test(agent-storage): 隔离 Chroma 测试数据写入` 提交；提交只包含 `agent/tests/conftest.py`，不包含 Chroma SQLite 或前端文件。

### 14.2 最终精简复验

| 验收项 | 命令或方式 | 结果 |
| --- | --- | --- |
| Python P2 安全、SSE、Trace、网关 | `python -m pytest -q agent/tests/test_internal_service_auth.py agent/tests/test_sse_streaming.py agent/tests/test_trace_and_logging.py agent/tests/test_gateway_test_provider.py` | `15 passed` |
| Java 全量测试 | `mvn -f backend/pom.xml test` | `129 tests`，0 failures，0 errors，`BUILD SUCCESS` |
| Frontend 类型检查和构建 | `npm --prefix frontend run build` | `vue-tsc && vite build` 通过，3469 modules transformed；仅保留既有 Sass/大 chunk 警告 |
| 基础设施测试 | `python -m pytest -q scripts/infra/tests` | `20 passed` |
| Windows Compose | `docker compose -f compose.yaml -f compose.dev.yaml -f compose.windows.yaml --env-file .env.windows config --quiet` | PASS |
| 五服务健康 | Compose/inspect | Frontend、Backend、FastAPI、PostgreSQL、Redis 均为 `running/healthy` |
| 普通 AI 请求 | 临时确定性 Provider，经 Frontend → Java → Python | HTTP 200，可信角色为 `USER` |
| SSE 短流 | 1 秒确定性事件流 | 5 个事件，`[DONE]=true` |
| SSE 心跳 | 1.3 秒确定性心跳流 | 5 个心跳，`[DONE]=true` |
| SSE 客户端取消 | 客户端关闭后查询 Python 状态 | `state=cancelled` |
| 测试 Provider 收尾 | 恢复 `SSE_TEST_MODE=false` 后检查 OpenAPI | `/ai/test/sse` 与 `/ai/test/proxy/{status_code}` 均不存在 |
| 泄漏扫描 | Compose 渲染、五容器 inspect/环境、进程参数、最近日志和 P2 新增内容 | 采集失败 0；已知 Secret、内部令牌、JWT Secret、JWT、模型 Key 命中均为 0 |

此前第 6 节记录的生产 Nginx 267.4 秒真实长流、49 个心跳和 `[DONE]=true` 证据继续有效，本次按门禁要求未重复执行。

### 14.3 HEAD、工作区与最终状态

- 最终验收代码 HEAD（独立文档提交前）：`8285fe54f6be75a8170e9becc3b784385bd7ff29`。
- 文档更新前最终 `git status --short` 无输出，工作树和暂存区均为空；Chroma 基线哈希保持不变。
- 本章通过独立提交 `docs(infrastructure): 完成 P2 Windows 最终验收闭环` 固化；该文档提交的完整 HEAD 由 Git 提交记录给出，避免文档自引用提交哈希。
- 状态由 `P2_NOT_ACCEPTED` 更新为 `P2_ACCEPTED_WINDOWS` 的依据是：前端文件已由用户独立处理；测试不会再次修改 tracked Chroma 数据库；全部精简复验通过；五服务 healthy；泄漏扫描命中数为 0；文档提交后工作树和暂存区保持为空。
- `P1.5-Linux: BLOCKED_EXTERNAL_ENVIRONMENT` 继续保留。
