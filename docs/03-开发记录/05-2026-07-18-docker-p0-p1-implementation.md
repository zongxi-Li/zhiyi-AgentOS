# Docker 基础设施重构 P0/P1 实施报告

日期：2026-07-18

冻结基线：《知弈 AgentOS Docker 基础设施重构 RFC v1.1》

实施范围：P0、P1；未引入 RFC 排除的组件。

## 1. 仓库现状审计和差异

实施起点为 Git `9b34b1a0bfc8fc35ce223eba5895e1b2903abf4e`。审计发现：

- 原有 Compose 定义分散在根目录和 `docker/`，开发、生产重复维护，网络边界和卷命名不统一。
- Backend 依赖 PostgreSQL、Redis 和 FastAPI；FastAPI 运行时代码不直接依赖 PostgreSQL 或 Redis，因此没有把 FastAPI 加入 `data-network`。
- 原 Flyway SQL 存在宽泛的条件式建表/建索引，无法可靠暴露 Schema 漂移；已有数据库也没有指纹审计和显式 baseline 门禁。
- AgentOS SQLite 缺少固定 WAL/busy timeout、进程级单实例门禁和可验证的一致性备份。
- Secret 过去主要依赖环境变量或只声明挂载，缺少运行用户实际读取、来源文件隔离和负向权限验证。
- 原部署没有覆盖 PostgreSQL 全局对象、Redis RDB 状态、上传文件、AgentOS 数据、版本清单和校验文件的一体化恢复闭环。
- Redis 当前用于 Spring Cache、会话辅助等可重新生成数据，本阶段归类为 `rebuildable-cache`；Redis 恢复失败不损坏业务主数据，但上线前必须清空并重新预热。
- Docker Engine 实测为 rootful：`DockerRootDir=/var/lib/docker`，SecurityOptions 只有 seccomp/cgroupns；没有 rootless 或 userns-remap。
- 旧的六个生产容器和旧卷 `docker_postgres_data`、`docker_redis_data`、`kinlin_ai_postgres_data` 均仍存在，未删除、未覆盖。

## 2. 实际修改文件

| 范围 | 文件 |
| --- | --- |
| Canonical Compose | `compose.yaml`、`compose.dev.yaml`、`compose.prod.yaml`、`compose.observability.yaml`、`.env.example`、`.dockerignore` |
| 兼容入口与启动 | `docker/docker-compose.yml`、`docker/docker-compose.dev.yml`、`docker/docker-compose.prod.yml`、`dev.ps1`、`dev.sh` |
| AgentOS SQLite | `agentOS/src/agentos/stores/sqlite_workflow_store.py`、`agent/app/execution/instance_lock.py`、`agent/app/execution/runtime.py`、`agent/app/operations/workflow_backup.py`、`agent/app/operations/__init__.py`、`agent/tests/test_sqlite_workflow_store.py` |
| FastAPI 运行与健康 | `agent/app/config.py`、`agent/app/main.py`、`agent/app/paths.py`、`agent/Dockerfile`、`agent/docker-entrypoint.sh` |
| Backend 数据与健康 | `backend/pom.xml`、`backend/src/main/resources/application*.yml`、`HealthController.java`、`SecurityConfig.java`、`JwtAuthenticationFilter.java`、`Role.java`、`RoleMapper.java`、`backend/Dockerfile*`、`backend/docker-entrypoint.sh`、`backend/.dockerignore` |
| Flyway | `V1__init_schema.sql` 至 `V6__upsert_builtin_roles.sql`、`docker/flyway/Dockerfile`、`docker/flyway/entrypoint.sh` |
| PostgreSQL/Redis | `docker/postgres/Dockerfile`、`docker/postgres/secret-entrypoint.sh`、`docker/postgres/init-app-role.sh`、`docker/redis/Dockerfile`、`docker/redis/entrypoint.sh`、`docker/redis/healthcheck.sh` |
| Frontend 容器 | `frontend/Dockerfile*`、`frontend/nginx.conf`、`frontend/nginx-main.conf`、`frontend/.dockerignore` |
| 基础设施脚本 | `scripts/infra/common.py`、`init_secrets.py`、`preflight.py`、`schema_audit.py`、`baseline_existing.py`、`backup.py`、`restore.py`、`firewall.py` 及 `scripts/infra/tests/` |
| 文档 | `README.md`、`docs/02-架构设计/07-docker-infrastructure-rfc-v1.1.md`、本文档、`.gitignore` |

根目录原有未跟踪 `docker-compose.yml` 没有纳入提交或删除；兼容入口使用已跟踪的 `docker/docker-compose*.yml` 转向 Canonical Compose。

## 3. Schema 指纹与 Flyway 双路径实现

### 全新数据库

空库审计实测结果：

```text
reportId=783b92ed-aadb-4db6-ab79-b15ac5615b5a
state=empty
baselineVersion=null
fingerprint=66e4d20bdaa6119a0abcaa9dd31d74b8c3dd468d5925820ca8f350f17362db26
```

随后由 Flyway 从 V1 顺序执行到 V6。迁移后的审计结果为：

```text
reportId=83c93d53-3d94-423a-bb71-31cf9548ccdc
state=managed
baselineVersion=null
fingerprint=e0a194ff3ec5ad665d17cfc3a50796825c9365057e52fc2ec315797059803d3a
history=1:true,2:true,3:true,4:true,5:true,6:true
```

### 已有数据库

`schema_audit.py` 只读提取表、列、索引和 Flyway 历史，分类为 `empty`、`managed`、`legacy` 或 `drift`。只有确定的 `legacy` 版本可进入 `baseline_existing.py`；执行时必须同时提交 deployment ID、报告 ID、原指纹和审计识别版本。脚本显式拒绝版本 0、报告不匹配、指纹变化和 drift。生产配置以及 Flyway 容器均固定 `baselineOnMigrate=false`。

迁移 SQL 不再用大范围 `IF NOT EXISTS` 掩盖漂移；V5 对兼容对象执行类型和约束定义检查，V6 使用稳定 UUID、`stable_key` 和受控 UPSERT 写入内置角色。

## 4. 备份、恢复和 SQLite 一致性结果

维护窗口内停止 Frontend、Backend 和 FastAPI 后，成功生成最终全量备份：

```text
.tmp-backups/kinlin-test-rfc11-20260717T161114Z
```

备份包含 PostgreSQL 自定义格式数据库、`pg_dumpall --globals-only --no-role-passwords` 全局对象、Backend 上传卷、AgentOS 数据卷、AI 缓存卷、SQLite Backup API 副本、Redis RDB、Schema 审计、Git/镜像/Compose 清单和 `SHA256SUMS`。共校验 11 个条目；密码、角色密码哈希和认证连接串扫描为空。

Redis 在归档前完成 BGSAVE，证据为：

```text
dbsize=1
rdb_last_bgsave_status:ok
sample_read_ok type=string key_sha256=2c974f...4947a
```

最终使用新的 `kinlin-restore6-rfc11` 实例 ID 和全新 Secret/卷完成隔离恢复：

```text
checksums=verified
postgresSuccessfulMigrations=6
redis.keyCount=1
redis.sampleReads=1
redis.persistence=ok
sqlite.integrity=ok
sqlite.tasks=0
sqlite.runs=0
restored schema fingerprint=e0a194ff3ec5ad665d17cfc3a50796825c9365057e52fc2ec315797059803d3a
```

前四次演练分别暴露 SQLite WAL 只读挂载、PostgreSQL bootstrap 角色、Redis AOF 优先级和 SQLite WAL 只读复核问题；脚本逐项修复后重新使用全新实例 ID 验证。失败演练实例仍保留，未执行破坏性清理。

SQLite 运行态实测：`journal_mode=wal`、`busy_timeout=5000`、`synchronous=2(FULL)`、`integrity_check=ok`。FastAPI 命令行固定 `--workers 1`，进程锁阻止第二实例共享同一 Workflow Store。

## 5. Canonical Compose、网络和卷结构

唯一结构源为 `compose.yaml`：

```text
Frontend -- web-network(internal) -- Backend
                                      |
                                      +-- agent-network(egress) -- FastAPI
                                      |
                                      +-- data-network(internal) -- PostgreSQL / Redis / schema-tool
```

- Frontend 只加入 `web-network`，仅访问 Backend。
- FastAPI 只加入 `agent-network`，不发布端口，不解析 PostgreSQL/Redis；实测连接 Backend:8080 返回 `connect_ex=111`，因为 Backend 只监听 web-network 地址。
- PostgreSQL 和 Redis 只加入 `data-network`，不发布宿主机端口。
- Backend 加入三个网络，是唯一可访问 FastAPI 的业务入口。
- `agent-network` 允许外部出站，FastAPI 实测访问外部 HTTPS 返回 200。Backend 和 FastAPI 都可能具备出站能力；P0/P1 只保证入站和容器横向隔离，不实现域名级出站控制。

卷名均包含实例 ID：

```text
kinlin-test-rfc11_postgres_data_v11
kinlin-test-rfc11_redis_data_v11
kinlin-test-rfc11_agentos_data_v11
kinlin-test-rfc11_backend_uploads_v11
kinlin-test-rfc11_ai_cache_v11
```

启动、备份、恢复均核验实例 ID、卷标签和数据 marker；恢复拒绝同 ID或已存在的目标卷。

## 6. Secret 权限与实际读取验证

Compose Secret 是 bind mount，不使用 Compose `uid/gid/mode`。Backend、FastAPI、Flyway、PostgreSQL 和 Redis 的最小 root 入口先复制 Secret 到 tmpfs、设置独占权限、封闭 `/run/secrets` 来源目录，再降权或交给官方入口：

```text
backend: source denied, target readable, UID=10001, target mode=0400
FastAPI: source denied, target readable, UID=10002, target mode=0400
Frontend: UID=10003
Flyway: target UID=10004, target mode=0400
PostgreSQL: source denied, target readable, UID=70, target mode=0400
Redis: source denied, tmpfs config readable, UID=999
```

Spring Boot 通过 configtree 消费 tmpfs 文件；FastAPI 通过 `*_FILE`；PostgreSQL 通过重写后的 `POSTGRES_PASSWORD_FILE`；Redis 通过只读 tmpfs 配置。未回退到明文环境变量、宽松权限或 root 常驻。

## 7. 自动化测试和实际命令结果

| 验收 | 实际结果 |
| --- | --- |
| Python/基础设施测试 | `19 passed in 0.42s`，包含 baseline 版本 0/负数拒绝、审计后 Schema 变化拒绝、网络卷、恢复全局对象和防火墙计划测试 |
| Backend Maven | `Tests run: 109, Failures: 0, Errors: 0, Skipped: 0`，`BUILD SUCCESS` |
| Frontend | `vue-tsc && vite build` 成功，3076 modules transformed |
| Compose | Canonical dev/prod 与兼容 dev/prod 共四组 `config --quiet` 通过 |
| 五服务启动 | source stack 五个服务均为 `healthy` |
| 健康语义 | Backend liveness=UP；readiness PostgreSQL/Redis=true；模型依赖独立为 DEGRADED/UNCONFIGURED 且 `affectsReadiness=false` |
| FastAPI 健康 | liveness=UP；readiness data/packs/store=true；模型依赖不影响 readiness |
| 网络负向测试 | Frontend 仅有 web；FastAPI 仅有 agent；FastAPI→Backend TCP 拒绝；FastAPI 无 data-network |
| 备份恢复 | 第六个全新实例完整恢复成功，Schema 指纹、Redis 键数、SQLite 完整性一致 |
| Secret 负向测试 | Backend/FastAPI/PostgreSQL/Redis 运行 UID 均不能读取 `/run/secrets` 原文件，能读取自己的 tmpfs 目标 |
| 预检 | 本地网关和远程私网网关两种模式均输出通过；远程模式标记 `firewallRequired=true` |
| 防火墙 | 在 Windows 工作站生成 nftables 计划，包含原规则备份、先 allow 后 drop、回滚和验证命令；未在无 nftables 的工作站实际改规则 |

构建期间一次 Docker Hub 元数据请求返回 EOF，单独重试后 Redis 与 Flyway 镜像均构建成功，不是代码失败。

## 8. 未完成项和风险

- Docker Desktop 对 internal `web-network` 的宿主机端口转发实测不可达，虽然 Compose 明确绑定 `127.0.0.1:8080` 且容器内链路健康。生产基线必须在 rootful Linux Docker Engine 复验同机 HTTPS 网关入口；未通过前不得上线。
- 远程网关防火墙只完成可预览、可备份、失败自动回滚和人工恢复脚本及单元测试；当前 Windows 工作站没有 nftables/firewalld/ufw，实际规则变更必须在目标 Linux 主机演练。
- P2 的 Java AI 网关统一鉴权、内部令牌全链路、SSE 空闲超时/心跳/最大时长/取消传播、Trace ID 和 Nginx—Java—Python 非缓冲验证尚未实施。
- P3 的完整只读文件系统、capability 收敛、amd64/arm64、在线/离线发布和依赖漏洞治理尚未实施。Frontend 构建仍有 Sass legacy API、大 chunk 警告；镜像构建时 npm audit 报告 20 个依赖漏洞，需在 P3 处理。
- P4 的真实旧数据副本迁移、生产级故障注入、回滚时限和完整验收尚未实施；本轮只完成测试数据的隔离备份恢复闭环。
- PostgreSQL Workflow Store 未完成，因此 FastAPI 水平扩容仍被禁止。

## 9. P2 前置条件和下一阶段清单

进入 P2 前必须完成：

1. 在目标 rootful Linux Docker Engine 复验 `127.0.0.1` Frontend 入口和同机 HTTPS 网关；远程模式则演练防火墙计划、备份、验证失败自动回滚和人工恢复。
2. 选定生产、测试、迁移演练的不同 `KINLIN_DEPLOYMENT_ID`，在真实旧数据的备份恢复副本上运行 Schema 审计；任何 `drift` 都停止迁移。
3. 冻结 Java→FastAPI 内部令牌协议和路由清单，确认所有浏览器流量只进 Backend。
4. 实现并测试 Trace ID 贯穿 Nginx、Java、Python。
5. 将 SSE 240 秒定义为空闲超时，增加心跳、可配置最大时长、客户端取消传播，并进行全链路非缓冲和长连接测试。
6. 保持模型 Provider 为独立 dependency 状态，不得把模型故障合并进 liveness/readiness。
7. 保持旧部署和本轮演练证据，直到 P4 迁移验收和一个发布周期兼容窗口结束。

计划提交按职责拆分，提交消息统一使用 `<英文类型>(<稳定模块名>): <中文描述>`。
