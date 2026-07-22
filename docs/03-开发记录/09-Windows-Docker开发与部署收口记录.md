# Windows Docker 开发与部署收口记录

日期：2026-07-19（2026-07-22 增补 Windows 开发启动优化验收）

## 1. 当前结论与范围

本记录以 Windows 11、Docker Desktop、Linux containers、`linux/amd64` 为唯一验收范围，覆盖高效开发、稳定运行、简单部署、数据持久化和基础备份恢复。P0、P1、P1-Windows、P2、P3 已有实现和历史报告继续保留，但 P3 的跨平台及企业门禁不再阻塞本范围。

```text
DOCKER_WINDOWS_DEVELOPMENT: ACCEPTED
DOCKER_WINDOWS_DEPLOYMENT: ACCEPTED
LINUX_KYLIN_SUPPORT: DEFERRED
ARM64_SUPPORT: DEFERRED
ENTERPRISE_SECURITY_GATE: DEFERRED
```

以上结果不得描述为 Linux、麒麟、ARM64、正式企业安全审批或企业级生产发布验收。现有 Trivy、SBOM 和漏洞报告未删除，也未宣称其中的 Critical/High 已修复；它们在当前范围内仅作为信息报告。

## 2. Windows 开发入口

日常入口为一个 PowerShell 命令：

```powershell
.\scripts\infra\windows\up.ps1
```

- `up.ps1` 默认复用现有镜像、Maven/Node/Python 缓存和容器配置；只有 Dockerfile、POM 或依赖变化时使用 `-Build`。
- `down.ps1` 不使用 `-v` 或 `--volumes`，不会删除数据卷。
- `status.ps1`、`logs.ps1`、`diagnose.ps1`、`restart-service.ps1`、`clear-backend-source-cache.ps1` 均通过 PowerShell AST 解析和脚本契约测试。
- Windows 开发环境将宿主 `backend/src` 只读挂载到 `/kinlin-host/backend-src`；`/app/src` 是 deployment 独立、`nocopy` 的 named volume。宿主源码始终是唯一事实来源，named volume 只承载可重建开发缓存。
- 容器启动与 `restart-service.ps1 -Service backend` 调用同一个加锁 rsync 脚本。无变化时跳过 Maven；新增或修改时执行默认依赖语义的 `mvn -B -ntp -DskipTests compile`；发生删除时先清理 `target/classes` 和 `target/generated-sources` 再编译。
- `restart-service.ps1 -Service backend -FullRestart` 保留显式硬重启；没有增加持续文件监听守护进程。
- Backend 开发镜像首次 `dependency:go-offline` 构建约 200.6 秒，属于镜像层一次性成本；镜像内 `/opt/kinlin-m2/repository` 已实测存在，新 Maven named volume 会从该目录预热。

### 2.1 源码缓存生命周期

- 同步使用 `rsync -rltc --delete`，锁文件位于 deployment 独立的 Backend build cache；锁等待上限 120 秒。
- `down.ps1` 不删除源码缓存；业务备份白名单不包含该缓存；业务数据卷清理脚本会按 lifecycle 标签保留该缓存。
- 只有以下显式命令会删除源码缓存，并且要求容器已停止、完整 deployment ID、危险操作开关及卷标签全部匹配：

```powershell
.\scripts\infra\windows\clear-backend-source-cache.ps1 `
  -ConfirmInstanceId kinlin-win-p1-001 `
  -IUnderstandDevelopmentCacheWillBeDeleted
```

### 2.2 2026-07-22 实测结果

优化前日志基线：五服务从最早容器启动到 Frontend ready 约 99.5 秒；Backend 从容器启动到 Spring Boot started 约 88.6 秒，其中从 Windows bind mount 执行 javac 全量编译 139 个源文件耗时约 64.4 秒。

优化后在同一 Windows 11、Docker Desktop、同一 deployment 和保留业务数据卷条件下，空源码缓存启动的 Compose readiness 为 19.94 秒。关键分段均相对最早容器启动时点：

| 分段 | 实测 |
|---|---:|
| PostgreSQL 进程 ready | 0.32 秒；PostgreSQL/Redis 健康依赖门禁均在 1.40 秒内通过 |
| Redis ready | 0.29 秒 |
| Frontend Vite ready / 可访问 | 2.51 秒；HTTP 200 |
| AI application startup / 首个 readiness | 7.58 秒 / 9.36 秒 |
| Backend 首次 rsync（184 文件） | 4.57 秒 |
| Backend javac（139 文件，Linux named volume） | 4.61 秒 |
| Backend Spring Boot started | 19.64 秒 |
| 五服务 Compose readiness | 19.94 秒；含预检的入口总时间约 22.73 秒，镜像构建不计入 |

五个规定场景均已实测：

| 场景 | 结果 |
|---|---|
| 空缓存首次启动 | 通过；缓存卷由显式命令删除后重建，业务卷未删除，五服务 19.94 秒 ready |
| 无修改重启 | `unchanged`；跳过 Maven，2.64 秒完成 |
| 单 Java 文件修改 | `changed`；默认 Maven 全依赖编译，10.81 秒恢复 ready |
| 新增 Java 文件 | `changed`；140 个源文件编译，对应 class 存在，12.56 秒恢复 ready |
| 删除 Java 文件 | `deleted`；清理并重建 classes，源文件和旧 class 均不存在，12.83 秒恢复 ready |

两个并发同步调用实测总耗时 3.30 秒；一个立即获得锁，另一个等待 1.71 秒后才进入 rsync，未发生并行同步。Frontend 在 Windows 开发覆盖层仅等待 Backend `service_started`，启动与 Java 编译并行；五个 `healthcheck.start_interval: 1s` 也只存在于该覆盖层。生产 Compose、生产镜像、部署包、Secret、网络、业务数据卷、API 和数据库迁移均未改变。

本次增补复验：`python -m pytest -q scripts/infra/tests scripts/release/tests` 为 49 passed；12 个 Windows PowerShell 脚本 AST 解析无错误；标准开发、Windows 开发、生产、Windows 生产和 release Compose 均通过 `config --quiet`。

## 3. Windows amd64 部署模式

`compose.windows.prod.yaml` 与 `compose.yaml`、`compose.prod.yaml` 组合使用，明确完成以下约束：

- 六个运行/迁移服务均固定 `platform: linux/amd64`；
- 所有 `build` 均通过 `!reset null` 移除，只使用已构建镜像；
- 不挂载 Frontend、Backend 或 FastAPI 源码，不启用 DevTools、Vite、Uvicorn reload 或调试端口；
- 仅 Frontend 发布 `127.0.0.1:${KINLIN_HTTP_PORT}:8080`；
- PostgreSQL、Redis、Backend、FastAPI 只保留容器端口；
- PostgreSQL、Redis、AgentOS、上传和 AI cache 使用 deployment ID 隔离的 named volume；
- 保留 read-only root、capability allowlist、Secret 文件、Java AI 鉴权、Java-Python 内部令牌和健康检查；
- Windows 包使用四个可配置 `/28` 子网，保持 web/agent/data/ingress 边界不变，同时避免 Docker Desktop 默认地址池被多套本地栈耗尽。

PostgreSQL 初始化脚本已烘入 Windows amd64 镜像，包不依赖仓库源码。Flyway 迁移 SQL 作为非敏感运行资产随包携带。

## 4. 简单部署包

最终包位置：

```text
artifacts/windows/kinlin-ai-windows-amd64/
```

包包含需求指定的 `compose.yaml`、`compose.windows.prod.yaml`、`.env.example`、`images.tar`、启动/停止/状态/日志/备份/恢复脚本和 `README.md`，另含必要的 `migrations/` 及隐藏运行辅助目录 `.kinlin/`。

```text
images.tar bytes: 809601536
images.tar sha256: 29581045f320f416121708a1d09d5192f6fc93ddd16a40280734f3172bf15084
package source commit: 9aae26d06af53954221cf809c5619840ef53e23f
```

生成器拒绝覆盖已存在包；构建和调试中产生的不完整包均改名为 `incomplete-*` 保留，没有删除旧包。最终包扫描结果：真实 `.env`、Secret、数据库/SQLite/RDB、上传、测试数据、`node_modules`、Maven `target`、Python venv 命中数均为 0。AI 镜像内 `.db`、`.sqlite*`、`.rdb` 命中为 0。

## 5. 真实部署验收

源实例：`kinlin-win-deploy-0719a`，Frontend `127.0.0.1:18100`。

恢复实例：`kinlin-win-restore-0719b`，Frontend `127.0.0.1:18101`。

| 验收项 | 结果 |
|---|---|
| 五个 Windows amd64 镜像构建 | 通过；Frontend、Backend、FastAPI、PostgreSQL、Redis 均为 amd64 |
| Flyway | 复用现有已验证 amd64 辅助镜像；6 个迁移成功/幂等校验通过 |
| `docker save` / `docker load` | 通过；移除本轮 Windows 标签后重载，六镜像 ID 和架构前后一致 |
| 包启动 | 通过；使用包脚本、`--pull never --no-build` |
| 健康状态 | 源实例 5/5 healthy；恢复实例 5/5 healthy |
| Frontend | 源实例 HTTP 200；恢复实例 HTTP 200 |
| 端口边界 | 每个实例仅 1 个发布端口，均为 Frontend loopback |
| 普通 AI | Frontend -> Nginx -> Java -> Python Workflow metrics HTTP 200 |
| SSE | Java 鉴权链短流 6 个事件及 `[DONE]`；心跳流断言通过 |
| 容器重启持久化 | PostgreSQL 用户可重新登录；指定 Workflow task 可查询；上传文件内容不变 |
| 备份 | 新目录 `kinlin-win-deploy-0719a-20260719T063814Z`；schema managed；SHA256SUMS 生成 |
| 恢复 | 校验和通过；PostgreSQL 6 迁移、Redis、SQLite integrity=ok、2 tasks 恢复到新 ID |
| 恢复后业务数据 | 登录 200、Workflow task 存在、上传文件存在、AI metrics 200 |
| 泄漏扫描 | 已知 Secret/JWT 0；JWT pattern 0；Authorization Bearer 0；包禁止文件 0 |

恢复过程中，当前 Docker Desktop 因保留大量历史测试网络而出现默认地址池耗尽。没有执行 network prune，也没有删除旧容器、卷、镜像、包或用户数据；改为为 Windows 包配置 deployment 独立的小型子网后完成恢复实例启动。中途重建的仅是本轮新恢复实例的 PostgreSQL/Redis 容器，原 named volume 和恢复数据保持不变。

## 6. 最终精简复验

| 范围 | 命令 | 结果 |
|---|---|---|
| P2 安全、SSE、Trace、网关 | `python -m pytest -q agent/tests/test_internal_service_auth.py agent/tests/test_sse_streaming.py agent/tests/test_trace_and_logging.py agent/tests/test_gateway_test_provider.py` | 15 passed；tracked Chroma SHA-256 不变 |
| Java | `mvn -B -ntp test` | 129 passed，0 failures/errors/skipped |
| Frontend 类型和构建 | `npm run build` | `vue-tsc` 和 Vite build 通过 |
| 基础设施与发布脚本 | `python -m pytest -q scripts/infra/tests scripts/release/tests` | 40 passed |
| Compose | 根目录 Windows prod 组合与包内组合 `config --quiet` | 均通过 |
| Backend 连接错误测试 | `mvn -Dtest=AiProxyServiceTest test` 连续两次 | 均 5 passed |

Java 全量复验曾暴露测试使用“临时端口关闭后必然立即拒绝连接”的 Windows 时序竞态，以及本地测试 HTTP server 1 秒预算过紧。修复仅使测试确定性地产生 `ConnectException`，并将非超时用例测试预算提高到 5 秒；生产网关超时、503/504 映射和业务代码未改变。

## 7. 保留边界

- Secret、JWT、内部令牌、模型 Key、数据库和 Redis 密码继续只通过 Secret 文件进入运行时，不写入 Git 或日志。
- Java 仍是客户端可见 AI 请求的统一鉴权边界，Java-Python 内部令牌继续启用。
- 普通停止和备份脚本不删除卷；恢复拒绝覆盖已有 target volume，要求新的 deployment ID。
- `KINLIN_DEPLOYMENT_ID` 继续决定独立容器、网络和五类数据卷。
- 本轮没有修改冻结的数据迁移语义、Workflow Store 架构、数据库权威数据或 P4 生产迁移内容。

验收代码 HEAD（文档提交前）：`1142986bc1a283fd2acb748fd296babf0c363e2e`。
