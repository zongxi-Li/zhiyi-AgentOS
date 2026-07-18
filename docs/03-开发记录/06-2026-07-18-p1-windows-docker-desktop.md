# P1-Windows Docker Desktop 本地开发环境验收报告

> 验收日期：2026-07-18
>
> 冻结生产基线：《知弈 AgentOS Docker 基础设施重构 RFC v1.1》
>
> 实施前 HEAD：`e862bbb9df73fcf59ead9036eefdfabe6cc09f50`
>
> 验收边界：Windows 11 + Docker Desktop `desktop-linux`，不代表 Linux/麒麟生产验收

## 1. 实际修改文件

| 范围 | 文件 |
| --- | --- |
| Windows Compose | `.env.windows.example`、`compose.windows.yaml`、`docker/debug-proxy/Dockerfile`、`.gitignore` |
| 开发镜像与缓存 | `compose.dev.yaml`、`.dockerignore`、`agent/Dockerfile.dev`、`agent/docker-entrypoint-dev.sh`、`backend/Dockerfile.dev`、`backend/docker-entrypoint-dev.sh`、`backend/.dockerignore`、`frontend/Dockerfile.dev`、`frontend/docker-entrypoint-dev.sh`、`frontend/.dockerignore` |
| Windows 运维 | `scripts/infra/windows/_common.ps1`、`preflight.ps1`、`up.ps1`、`down.ps1`、`restart-service.ps1`、`logs.ps1`、`status.ps1`、`clean-build-cache.ps1`、`diagnose.ps1`、`remove-data-volumes.ps1` |
| 测试与备份兼容 | `scripts/infra/tests/test_windows.py`、`scripts/infra/backup.py` |
| 文档 | `README.md`、本报告 |

`compose.prod.yaml`在本阶段没有修改；非 root、Secret 文件读取、内部网络、唯一公开入口、实例卷隔离、Flyway 双路径、SQLite 单实例和 Linux 防火墙门禁均未被削弱。

## 2. Windows Compose 合并结构

标准启动命令：

```powershell
docker compose `
  -f compose.yaml `
  -f compose.dev.yaml `
  -f compose.windows.yaml `
  --env-file .env.windows `
  up -d --build
```

推荐使用等价包装脚本：

```powershell
.\scripts\infra\windows\up.ps1
```

本次实测实例为 `kinlin-win-p1-001`，因保留旧部署的 `127.0.0.1:8080`，使用 `127.0.0.1:18088`完成验收；示例配置仍默认 8080。实测五个核心服务全部 healthy：Frontend、Backend、FastAPI、PostgreSQL、Redis。

```text
Host 127.0.0.1:18088
  └─ windows-ingress-network (non-internal)
       └─ Frontend
            └─ web-network (internal) ─ Backend
                 Backend ─ agent-network (egress) ─ FastAPI
                 Backend ─ data-network (internal) ─ PostgreSQL / Redis
```

`windows-ingress-network` 只有 Frontend；Backend、FastAPI、PostgreSQL、Redis 均没有加入。`debug-ports` profile 通过独立代理临时发布 `127.0.0.1:18080` 和 `127.0.0.1:18000`，关闭 profile 后两端口均不可达，业务容器本身不发布端口。

命名卷使用实例 ID：

- RFC 数据卷：`postgres_data_v11`、`redis_data_v11`、`agentos_data_v11`、`backend_uploads_v11`、`ai_cache_v11`。
- Windows 依赖卷：`frontend_node_modules`、`maven_cache`、`backend_build_cache`、`python_venv`、`pip_cache`。

所有卷的实际名均以 `${KINLIN_DEPLOYMENT_ID}_` 开头。第二实例 `kinlin-win-p1-002` 的 PostgreSQL 探针用户数为 0，而主验收实例中探针用户存在，证明数据卷没有共享。第二实例停止后卷仍保留。

## 3. 入口和网络矩阵

| 源 | 目标 | 实测结果 | 证据摘要 |
| --- | --- | --- | --- |
| Windows Host | Frontend | 成功 | `http://127.0.0.1:18088` 返回 HTTP 200 |
| Windows Host | Backend / FastAPI / PostgreSQL / Redis | 失败，符合预期 | 18080/18000/15432/16379 默认均不可达 |
| Frontend | Backend | 成功 | Backend 健康端点 HTTP 200 |
| Frontend | FastAPI / PostgreSQL / Redis | 失败，符合预期 | 目标名无法解析，返回码 2 |
| Backend | FastAPI / PostgreSQL / Redis | 成功 | FastAPI HTTP 成功，PostgreSQL/Redis TCP 成功 |
| FastAPI | Backend | 失败，符合预期 | `ConnectionRefused` / `connect_ex=111` |
| FastAPI | PostgreSQL / Redis | 失败，符合预期 | 目标名无法解析，返回码 2 |
| FastAPI | 外部 HTTPS | 成功 | `https://example.com` 返回 HTTP 200 |

Docker network inspect 证据：`windows_ingress` 为 `internal=false` 且只有 Frontend；`web` 为 `internal=true` 且只有 Frontend/Backend；`agent` 为 `internal=false` 且只有 Backend/FastAPI；`data` 为 `internal=true` 且只有 Backend/PostgreSQL/Redis。本阶段只保证入站和容器横向访问隔离；`agent-network` 允许外部出站，因此 Backend 和 FastAPI 均可能具备出站能力，未扩大范围实现域名级出站控制。

## 4. Secret 适配方式

Windows Secret 仍以文件形式从宿主机只读挂载到入口目录，容器入口先复制到 tmpfs，设置目标 UID/GID 和 `0400`，验证后再降权启动。该适配仅位于 Windows/dev 开发路径，Linux 生产仍保留宿主机 UID/GID 预置和负向权限门禁。

实测 Backend 和 FastAPI 的授权 UID 能读取 tmpfs Secret，原始挂载路径和未授权 UID 均不可读。对 5 个实际 Secret 值扫描了：

- Compose 渲染结果：0 命中。
- 五个容器环境：0 命中，无敏感环境变量赋值。
- 进程参数：0 命中。
- 最近日志和诊断包：0 命中。

`.env.windows.example` 只包含实例 ID、端口、路径和轮询开关等非敏感参数；`.env.windows` 和真实 Secret 目录被 Git 忽略。

## 5. 热更新和构建缓存结果

Docker Desktop bind mount 在本机上出现过文件内容已进入容器，但 Vite 和 WatchFiles 没有稳定收到事件的情况。因此实测 `.env.windows.example` 启用了仅针对 Vite 和 FastAPI 的可配置 1000 ms polling，没有对所有服务启用高频轮询。

| 项目 | 实测结果 |
| --- | --- |
| Vue/Vite 修改感知 | 408 ms |
| FastAPI 自动 reload | 365 ms，Uvicorn worker PID `236869 → 239262`，健康状态保持 |
| Spring Boot 稳定反馈路径 | `restart-service.ps1 backend`，不重建基础镜像；优化后约 67.3 s，应用自身启动 4.834 s |
| 无源码变更的暖构建 | 三个开发镜像 4.8 s，依赖层均命中缓存 |
| 普通源码变更构建 | 10.1 s；`apt`、Maven dependency resolve、`pip install`、`npm ci` 均显示 `CACHED` |
| Frontend 依赖目录 | Docker named volume，不覆盖 Windows 宿主机源码 |
| Maven / Python | Maven repo、Backend target、Python venv、pip cache 均使用实例命名卷 |

轮询开启后的单次 CPU 快照为 Frontend 2.59%、FastAPI 3.23%；之前无轮询快照为 Frontend 0.10%、Backend 0.49%、FastAPI 0.25%。这是本机时点样本，不是容量基准，可通过 `KINLIN_WINDOWS_POLL_INTERVAL_MS` 增大间隔降低开销。

Dockerfile 已调整为先复制依赖清单、安装依赖，再复制源码。开发入口额外使用依赖文件哈希，依赖清单不变时跳过重复安装。`.dockerignore` 已排除 Git、`node_modules`、`dist`、`target`、Python 缓存、`.venv`、日志、临时备份、release、IDE 缓存、本地数据和真实 Secret。

## 6. PowerShell 脚本清单

| 脚本 | 用途与安全边界 |
| --- | --- |
| `_common.ps1` | 路径、`.env.windows`、Compose 参数和 WSL 输出的共用处理 |
| `preflight.ps1` | 检查 Windows/`desktop-linux`、rootful Linux Engine、Compose、WSL2、Secret、合并配置、端口、资源与磁盘 |
| `up.ps1` | 先预检，再使用 BuildKit 启动五服务 |
| `down.ps1` | 停止并移除容器/网络，默认不删卷，不包含 `down -v` |
| `restart-service.ps1` | 只重启指定服务 |
| `logs.ps1` | 查看最近服务日志 |
| `status.ps1` | 显示当前实例、Compose 文件和服务状态 |
| `clean-build-cache.ps1` | 只清理 BuildKit 构建缓存，不清理数据卷 |
| `diagnose.ps1` | 生成脱敏诊断包，包含版本、WSL、健康、端口、网络、卷、磁盘、日志和连通性 |
| `remove-data-volumes.ps1` | 独立危险操作，必须显式输入完整实例 ID 二次确认 |

所有脚本 PowerShell Parser 错误数为 0。在带空格的项目路径 `C:\Users\LZX\Desktop\Kinlin P1 Windows Path` 中实际运行 `status.ps1` 和 `preflight.ps1`，均返回 0。`down.ps1` 运行前后实例卷数为 10/10，未删除卷。

## 7. 实际测试命令和结果

### 环境与预检

- Windows 11，32 逻辑 CPU，34,141,495,296 bytes 主机内存，工作盘可用约 114.9 GB。
- Docker context：`desktop-linux`。
- Docker Engine/Client：29.0.1；Docker Desktop：4.52.0；Compose：2.40.3-desktop.1。
- Engine：Linux amd64，内核 `6.6.87.2-microsoft-standard-WSL2`，15.51 GiB，rootful `/var/lib/docker`。
- WSL：默认 Ubuntu，WSL 2。BuildKit 已启用。
- `preflight.ps1` 实际返回 `P1-Windows preflight passed`。

### 自动化和构建

```text
python -m pytest -q scripts/infra/tests
20 passed

python -m pytest -q agent/tests/test_sqlite_workflow_store.py
3 passed

docker compose ... exec frontend npm run build
PASS，3090 modules，17.83 s

docker compose ... exec backend mvn -q test   # 显式使用 H2 测试 URL
PASS，exit 0

docker compose ... config --quiet
PASS，exit 0
```

Backend 首次测试继承了 Compose 的 PostgreSQL URL，110 个用例中出现 7 个 Spring context 错误；显式覆盖为 H2 测试 URL 后同一套件 exit 0。该过程是测试环境选择错误，不是忽略失败。Frontend 构建仅保留 Sass legacy API 和 chunk size 警告。`git diff --check` 通过，仅有 Windows CRLF 转换提示。

### 持久化、备份和完整性

在 PostgreSQL 写入固定探针用户、Backend 上传卷写入文件、AgentOS SQLite 写入 Workflow Task 后，重启 PostgreSQL、Backend 和 FastAPI，三类数据均保留。SQLite 实测为 WAL、`busy_timeout=5000`、`integrity_check=ok`、tasks=1。在线 SQLite Backup API 生成 20,480 bytes 一致性副本，副本 `integrity_check=ok`、tasks=1、runs=0。

完整备份实际运行两次：

1. `kinlin-win-p1-001-20260718T050225Z` 已生成数据文件，但 Docker Desktop 中的旧 manifest list 使 `docker compose images` 在版本清单阶段失败，因此没有 `manifest.json`/`SHA256SUMS`；该失败目录保留为证据，不宣称为成功备份。
2. 增加仅用于版本清单的 container-inspect fallback 后，`kinlin-win-p1-001-20260718T050340Z` 完整通过。其包含 PostgreSQL globals 652 bytes、database dump 17,813 bytes、Redis RDB 88 bytes、Backend uploads、AgentOS 数据与 SQLite 一致性副本、AI cache、Schema 审计、版本清单 2,971 bytes 和 `SHA256SUMS`。

成功备份的 SHA-256 校验失败数为 0，敏感模式扫描命中为 0。Schema 识别为 managed V1–V6，指纹为 `e0a194ff3ec5ad665d17cfc3a50796825c9365057e52fc2ec315797059803d3a`。Redis 备份前的 RDB 生成已确认，`dbsize=0`、`rdb_last_bgsave_status=ok`；当前 Redis 定义为可重建缓存，本次空缓存恢复失败不阻断业务数据验收，但仍会在恢复脚本中失败可见。

## 8. 性能变化

| 优化点 | 变化 |
| --- | --- |
| Frontend 文件所有权 | 从启动时递归 `chown` 约 64.7 s，改为构建期 `COPY --chown` |
| 依赖分层 | 普通源码变更不再重装 npm/Maven/pip 依赖 |
| 暖构建 | 三个服务 4.8 s |
| 源码变更构建 | 10.1 s，仅源码 COPY/后续层重新执行 |
| Backend 重启 | 从约 77.9 s 降为约 67.3 s，开发启动跳过 test compile |
| 热更新稳定性 | Docker Desktop 上改为可配置 1000 ms polling，以约 2.59%/3.23% 时点 CPU 换取稳定文件感知 |

这些数值是同一台本地机器的实测时点数据，用于本阶段前后对比，不作为生产容量承诺。

## 9. 未解决问题与风险

1. `P1.5-Linux: BLOCKED_EXTERNAL_ENVIRONMENT`：缺少麒麟/Linux 目标主机、SSH、真实 HTTPS 网关来源和独立拒绝来源/防火墙探测条件。本报告不使用 Docker Desktop/WSL 冒充 Linux 生产验收。
2. Linux 入口网络是否需要 RFC Amendment，仍必须在 rootful Linux 目标环境根据发布端口实测决定；Windows 专用 ingress 不修改生产结论。
3. Linux 宿主机 Secret UID/GID 正负向权限、rootful/userns-remap 门禁和远程防火墙计划/备份/自动回滚/人工回滚尚未验收。
4. Vite/FastAPI polling 会增加本地 CPU 消耗；默认间隔为 1000 ms，应在不需要时关闭或拉长。
5. Spring Boot 没有引入复杂热替换，源码反馈路径仍是 Maven 增量编译和重启容器，约一分钟。
6. Docker Desktop 的旧 manifest list 会使 `compose images` 失败；备份脚本已将实际容器 image inspect 作为可见 fallback，但不会静默忽略连实际容器也无法检查的情况。
7. 首次备份失败目录和 `kinlin-restore-rfc11` 至 `kinlin-restore6-rfc11` 演练实例/卷均保留。它们有 `com.kinlin.deployment-id` 隔离标识，当前卷上无法原地追加 Docker label；生命周期依据 P0/P1 报告和本清单管理，未执行删除或重建。
8. 仓库中在本阶段开始前已存在业务代码、图纸和未跟踪文件改动；本阶段未改动、未暂存它们。因此本阶段文件可在提交后干净，但整个共享工作树不能在不丢弃用户工作的前提下宣称 clean。

## 10. 是否具备进入 P2 代码开发的条件

**具备进入 P2 代码级开发的条件。** Windows 本地五服务、网络隔离、Secret 适配、依赖缓存、热更新、持久化、诊断和安全停机路径已完成实测。

该结论仅授权 P2 的代码开发和 Docker Desktop 联调，不授权 P2 生产发布验收，也不解锁 P3/P4 最终通过。后三者仍以 `P1.5-Linux` 在麒麟/rootful Linux 目标环境的真实验收为前置条件。
