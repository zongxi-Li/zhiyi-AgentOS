# P3 实施前只读审计

审计日期：2026-07-19（Asia/Shanghai）

审计基线：`c66800693df67130201816f7831309be88078c24`

审计边界：仓库、Windows 11 Docker Desktop `desktop-linux`、本地镜像和公开的 Docker Hub/PyPI 元数据。审计期间 `git status --short` 无输出，tracked Chroma SHA-256 保持 `5EB1A9E3C95075971A524FEF4D95CE08B68914272AAB2F6E34654D9EC54B3031`。

## 1. 当前镜像与 Dockerfile 现状

### 1.1 基础镜像、阶段和架构（问题 1–3）

| 服务 | 当前生产 Dockerfile 基础镜像 | 本机实际版本 | 阶段 | 当前本机架构 | 运行阶段内容 |
| --- | --- | --- | --- | --- | --- |
| Frontend | build=`node:24-alpine`；runtime=`nginx:alpine` | Node 24.18.0；Nginx 1.31.1；Alpine 3.23/3.24 | 多阶段 | linux/amd64 | 仅静态产物、Nginx、BusyBox/apk；无 Node/npm/源码 |
| Backend | build=`maven:3.9-eclipse-temurin-17`；runtime=`eclipse-temurin:17-jre-alpine` | Maven 3.9.16；Temurin 17.0.19+10 | 多阶段 | linux/amd64 | JRE、应用 JAR、wget、su-exec、iproute2、BusyBox/apk；无 Maven/JDK/源码 |
| FastAPI | `python:3.14-slim` | Python 3.14.5；Debian 13 | 单阶段 | linux/amd64 | Python、pip、gosu、应用 Python 源码和依赖；无编译器，但仍有 pip/apt/dpkg |

当前运行的是开发镜像：Frontend 与 FastAPI 含源码、依赖目录和热更新工具；Backend 含 Maven/JDK/源码和调试端口。开发镜像不作为发布最小化结论。

### 1.2 用户、目录和只读根文件系统（问题 4–5）

| 服务 | 容器入口用户 | 最终业务进程 UID:GID | WORKDIR | 必须可写 |
| --- | --- | --- | --- | --- |
| Frontend | 10003:10003 | 10003:10003 | 生产镜像 `/`（应统一为 `/usr/share/nginx/html`） | `/tmp` tmpfs（PID、client/proxy/FastCGI/uwsgi/scgi temp） |
| Backend | root 最小入口 | 10001:10001 | `/app` | `backend-uploads:/app/data/uploads`、`/run/kinlin-secrets` tmpfs、`/tmp` tmpfs |
| FastAPI | root 最小入口 | 10002:10002 | `/app` | `agentos-data:/app/data`、`ai-cache:/app/.cache`、`/run/kinlin-secrets` tmpfs、`/tmp` tmpfs |
| PostgreSQL | 官方/root 入口后 postgres | 官方 UID | 官方目录 | `postgres-data:/var/lib/postgresql/data`、`/run/kinlin-secrets`、`/var/run/postgresql`、`/tmp` |
| Redis | root 最小入口后 redis | 官方 UID | `/data` | `redis-data:/data`、`/run/kinlin-secrets`、`/tmp` |
| Flyway | root 最小入口后 10004 | 10004:10004 | 官方目录 | `/run/kinlin-secrets`、`/tmp` |

未提供上述 tmpfs/volume 就启用 `read_only` 时，Frontend 会因 Nginx PID/temp 失败；Backend 会因 Secret、监听地址文件、JVM temp 或上传目录失败；FastAPI 会因 Secret、SQLite/锁/缓存或文档临时文件失败。数据卷名和网络拓扑不得改变。

### 1.3 跨架构 Dockerfile 风险（问题 6）

- 三个业务 Dockerfile没有硬编码架构名、二进制下载 URL或 `uname -m` 分支。
- 当前 Backend runtime 标签 `eclipse-temurin:17-jre-alpine` 的 2026-07-19 清单只有 amd64，是实际 ARM64 阻断项；采用相同 Java 17.0.19 的 jammy 多架构变体。
- 当前 `flyway/flyway:9.22.3-alpine` 只有 amd64；同版本非 Alpine `flyway/flyway:9.22.3` 同时提供 amd64/arm64，可替换且不改变迁移引擎版本。
- 旧 `deploy-kylin.sh` 使用 GitHub `latest` 和 `uname -m` 拼下载 URL，且未映射 `aarch64` 到发布命名，不能用于 P3 发布。

## 2. amd64/arm64 依赖兼容矩阵

### 2.1 平台相关直接依赖（问题 7、9–11）

- Frontend 构建依赖中的 esbuild、Rollup、`sass-embedded` 使用平台包；lock v3 已包含 linux x64/arm64 和 glibc/musl 变体。浏览器运行产物为纯静态文件。
- Java 直接依赖均为 Java/JAR；未发现 `System.load*`、JNI、JNA、浏览器驱动或 Playwright/Selenium。Reactor Netty 传递依赖当前包含 `netty-transport-native-epoll:linux-x86_64`，ARM64 可回退纯 Java NIO，但发布制品不应携带错误架构 native JAR。
- Python 原生/平台依赖包括 PyYAML、NumPy、Pandas、lxml、psutil、pydantic-core、httptools、uvloop、watchfiles、aiohttp、bcrypt、cffi、cryptography、grpcio、jiter、mmh3、ONNX Runtime、orjson、ormsgpack、Pillow、pybase64、pypdfium2、rpds-py、tokenizers、xxhash、zstandard，以及 Chroma 的原生 wheel。
- PostgreSQL、Redis、Nginx、Maven/Temurin JDK、Node 和 Python选定官方系列均提供 linux/amd64 与 linux/arm64。Temurin Alpine 17 JRE的具体标签例外，必须换为 jammy。

### 2.2 Python 3.14 wheel 审计（问题 8、12–13）

2026-07-19 按当前解析版本查询 PyPI 文件元数据。下表只列兼容风险；其余纯 Python 依赖两架构等价。

| 依赖/基础项 | 当前版本 | amd64 | arm64 | 推荐解决方式 | 阻断 P3 |
| --- | --- | --- | --- | --- | --- |
| Python base | 3.14.5 slim-trixie | 官方镜像通过 | 官方镜像通过 | 固定可读版本+manifest digest | 否 |
| NumPy/Pandas/lxml/psutil/PyYAML | 2.5.1/2.3.3/6.1.1/7.2.2/6.0.3 | CP314 wheel | CP314 aarch64 wheel | 锁版本和全平台哈希，禁止 sdist | 修复前是 |
| uvicorn standard 原生链 | uvicorn 0.51.0；httptools 0.8.0；uvloop 0.22.1；watchfiles 1.2.0 | CP314 wheel | CP314 aarch64 wheel | 锁版本和哈希 | 修复前是 |
| Pydantic core | 2.46.4 | CP314 wheel | CP314 aarch64 wheel | 锁版本和哈希 | 修复前是 |
| Chroma | 1.5.9 | cp39-abi3 wheel | cp39-abi3 aarch64 wheel | 锁版本；两架构 smoke | 否 |
| ONNX Runtime | 1.27.0 | CP314 wheel | CP314 aarch64 wheel | 锁版本；禁止源码回退（该版本无 sdist） | 修复前是 |
| tokenizers/hf-xet/grpcio/orjson | 0.23.1/1.5.2/1.82.1/3.11.9 | wheel | aarch64 wheel | 锁版本和哈希 | 修复前是 |
| pypdfium2 | 5.12.1 | py3 platform wheel | py3 aarch64 platform wheel | 锁版本和哈希；不能用仅 `cp314` 文件名规则误判 | 否 |
| Java Netty native epoll | 4.1.101.Final x86_64 classifier | 可加载 | 错误架构，回退 NIO | 排除 native classifier并固定 NIO | 修复前是 |
| Temurin runtime Alpine | 17.0.19 | 可用 | 标签未发布 | 改 `17.0.19_10-jre-jammy` | 是 |
| Flyway Alpine | 9.22.3 | 可用 | 标签未发布 | 改同版本非 Alpine多架构标签 | 是 |
| npm平台包 | esbuild 0.21.5、Rollup 4.x、sass-embedded 1.100.0 | lock包含 | lock包含 | `npm ci`，两架构 build | 否 |

当前 Python 3.14依赖链存在双架构 wheel，不需要降到 3.13/3.12。风险来自宽松解析而非 3.14 本身：生产安装必须使用 exact+hash lock 和 `--only-binary=:all:`；任一平台 wheel消失即构建失败，不得静默源码编译。

## 3. 构建可重复性（问题 14–20）

1. Frontend `package-lock.json` 已提交，lockfileVersion=3，含 386 个 integrity，生产使用 `npm ci`。当前 Dockerfile `build:docker` 只跑 Vite，应改为完整 `npm run build` 包含 vue-tsc。
2. Python只有范围 requirements，无 lock/哈希；必须新增跨平台 hash lock，生产只读该 lock。
3. Maven由 Spring Boot 3.2.0 parent/BOM管理，无 SNAPSHOT、动态版本或额外 repository；多数版本可重复，但 Maven/JDK基础标签、插件元数据和仓库可用性未完全锁定。保留 POM，固定构建镜像、插件/直接显式版本，输出依赖/SBOM。
4. 构建依赖 Docker Hub、npm registry、Maven Central、PyPI；无 Git分支依赖。旧发布脚本依赖 `latest`、get.docker.com 和 GitHub latest，必须停用。
5. 基础镜像采用“可读精确版本标签 + manifest digest”双重记录；Dockerfile默认引用 digest，release manifest再次记录各平台最终 digest。
6. P3目标是“完全离线运行/安装”，不是“离线从源码重建”。后者还需要内部 OCI registry、npm/Maven/PyPI镜像和基础镜像缓存，作为后续独立能力。
7. BuildKit cache mount只缓存下载，不进入最终层；在 lock/hash和固定基础镜像前提下不改变依赖选择。发布构建不得从可变源码 cache复制产物，验收需要一次 `--no-cache`/clean build抽查。

## 4. Buildx Bake 设计（问题 21–27）

- Docker 29.0.1、Buildx 0.29.1、BuildKit 0.25.2已启用。当前 `desktop-linux` docker driver只报告 linux/amd64及 v2/v3，未报告 arm64；当前无原生或可用 QEMU arm64 builder证据。
- 采用单一 `docker-bake.hcl` 描述发布构建；Compose仍是运行拓扑权威，不把包含Secret/volume/network的Compose作为Bake输入，避免运行与发布职责混杂。
- 目标：`frontend`、`backend`、`ai-service`、`postgres`、`redis`、`flyway`、`runtime-dependencies`、`all`、`release-amd64`、`release-arm64`、`release-multiarch`。
- amd64/arm64使用完全相同Dockerfile，通过 BuildKit `TARGETARCH`只做验证/标签，不下载手工架构二进制。
- 多架构失败时允许本地保留已成功制品，但 release manifest不生成、发布状态失败，不能声明双架构完成。
- 报告分开记录 `cross-build passed`、`emulated smoke passed`、`native runtime unverified`；QEMU成功绝不等于麒麟/原生arm64通过。

## 5. 镜像安全与最小化（问题 28–37）

- Frontend业务进程直接非root；Backend/FastAPI容器入口以root处理 P0/P1 Secret，随后业务进程分别降到10001/10002。固定UID/GID必须保持。
- Frontend runtime删除Node/npm/源码；Backend runtime删除Maven/JDK/源码；FastAPI改多阶段，只复制锁定venv和必要源码，不复制build cache。三个runtime均不安装编译器、Git、curl或调试套件。
- Shell保留，因为 Secret入口和私有化诊断需要；配合只读根、非root业务进程、`no-new-privileges`、能力最小化、无宿主Docker socket、无额外工具控制风险。
- Frontend `cap_drop: ALL`。Backend/FastAPI最小root入口需要 `CHOWN,DAC_OVERRIDE,FOWNER,SETGID,SETUID`，su-exec/gosu降权后业务进程不保留effective capability。监听端口均大于1024。
- Nginx监听8080，PID和所有temp目录固定到`/tmp`；无需写`/var/cache/nginx`。
- Backend健康检查暂保留wget；FastAPI使用Python stdlib；Frontend使用BusyBox wget。移除这些工具前需新增应用内/静态二进制探针，不能把`nginx -t`当readiness。
- 当前没有Trivy/Grype/Syft可执行文件，但Docker Scout 1.18.3和`docker sbom`可用，BuildKit支持SBOM/provenance attestation。
- 默认门禁：Critical=0；High必须有版本化豁免；生成SPDX SBOM；记录镜像digest；已知Secret和模式扫描=0。扫描器不可用或数据库更新失败时发布失败，不得跳过。

## 6. 在线发布设计（问题 38–44）

- 当前 Docker config使用Desktop credential store，但没有配置registry auth条目；无可确认的正式registry/namespace。
- 使用 `KINLIN_REGISTRY`、`KINLIN_IMAGE_NAMESPACE`、`KINLIN_VERSION`参数化；建议 `${registry}/${namespace}/{frontend,backend,ai-service,postgres,redis,flyway}:${version}`，默认namespace `kinlin-ai`，发布时registry必填。
- 新增根`VERSION`作为仓库权威语义版本，并校验与Maven/npm版本一致；正式release要求Git tag `v<VERSION>`，开发候选可附加`-rc`，manifest记录完整Git SHA。
- 禁止latest。发布同时记录semver tag、`sha-<12>` tag和manifest digest。
- 国内/私有化在线发布应镜像化六个运行镜像，包括PostgreSQL、Redis、Flyway，避免目标环境访问Docker Hub。
- 每镜像先推不可变Git SHA tag，全部push/scan/SBOM成功后生成release manifest并最后发布semver引用；release manifest是可用性标志。部分push只算未引用的暂存制品。

## 7. 离线包目录与格式（问题 45–52）

六镜像均必须包含。amd64/arm64独立包，建议：

```text
kinlin-ai-<version>-linux-<arch>/
  VERSION
  manifest.json
  SHA256SUMS
  compose/compose.yaml
  compose/compose.prod.yaml
  config/.env.prod.example
  config/secrets/README.md
  images/<service>.tar.gz
  sbom/<service>.spdx.json
  scripts/{preflight,install,upgrade,rollback,backup,restore,diagnose}.sh
  docs/DEPLOYMENT.md
```

- 默认每镜像独立`docker save` tar后gzip，兼容性和失败重试优先；OCI archive可作为在线供应链内部格式，不作为麒麟安装必需格式。
- 当前目标环境zstd能力未知，Windows本机也未安装zstd，因此不把tar.zst设为唯一格式；未来可选zstd，同时保留gzip或原始tar。
- preflight同时比较`uname -m`、Docker server architecture和manifest architecture，将x86_64映射amd64、aarch64/arm64映射arm64，任一不匹配拒绝。
- 安装固定使用`docker compose --pull never --no-build up -d`，导入后核验六镜像存在及架构；可额外用隔离/代理日志证明无pull尝试。
- 打包只使用明确allowlist；扫描文件名和内容，拒绝`.env`、`.secrets`、私钥、数据库、SQLite、RDB、dump、node_modules、target、venv、cache、测试数据。生成SHA256SUMS前后各扫描一次。

## 8. 安装、升级和回滚（问题 53–59）

- 在线和离线共用同一JSON release manifest、版本/架构/Schema兼容规则和脚本库；只在镜像取得方式（pull或load）不同。
- 升级顺序：预检→校验release→核验deployment ID→最终备份→导入/拉取不可变镜像→Schema审计/兼容门禁→Flyway migrate→按依赖启动→readiness→smoke→原子写current manifest。
- manifest必须声明`schemaVersion`、`minCompatibleAppVersion`和`rollbackCompatible`。数据库迁移成功后，只有明确声明旧应用兼容新Schema才能自动回镜像；否则停止人工处置，优先前向修复或按P0/P1完整恢复到新实例。
- 允许自动镜像回滚：迁移未开始，或迁移无变化，或manifest明确backward-compatible且备份成功。迁移不兼容、Schema drift、备份/校验失败、数据恢复需求一律人工。
- rollback只能`compose stop/up`或`up --no-deps`切镜像，脚本静态测试拒绝`down -v`、volume rm、prune、Git checkout和覆盖备份。
- 发布包默认不重复包含上一个版本；部署端在`releases/<version>`保留旧manifest和镜像。可选“带前一版”包由发布系统显式生成。
- preflight拒绝降级、跨过manifest声明的不兼容版本、CPU架构不符、deployment ID不符、磁盘不足、Docker/Compose过低以及目标卷marker不符。

## 9. 当前环境可验收范围（问题 60–65）

- Windows Docker Desktop可真实完成：amd64 build/save/load、全新实例启动、健康、普通/SSE smoke、备份恢复回归、read-only/capability、SBOM/漏洞/Secret扫描、离线包校验和无pull安装。
- 这些能力已有P0–P2基础证据；P3必须用新镜像和新包再验收，不直接继承旧镜像结论。
- 当前arm64最多可先完成Dockerfile/Bake静态检查。创建QEMU builder成功后可标记cross-build和emulated smoke；不能标记原生运行、麒麟兼容、真实性能、Secret权限或防火墙通过。
- 仓库和Docker context中没有远程/云端原生arm64主机：`P3_ARM64_NATIVE_RUNTIME: BLOCKED_EXTERNAL_ENVIRONMENT`。
- P1.5仍为`BLOCKED_EXTERNAL_ENVIRONMENT`。状态必须区分`P3_ACCEPTED_WINDOWS_AMD64`、`P3_MULTIARCH_BUILD_ACCEPTED`和`P3_PRODUCTION_ACCEPTED`；当前目标最多是前两者，最后一项必须等待Linux/麒麟实机。
- 实施前阻断项是Python lock、Temurin/Flyway标签、Netty classifier、只读/capability和旧发布脚本；均有安全替代方案，不修改冻结迁移语义、网络、Secret模式、权威数据或Workflow Store，因此允许开始P3。

## 10. 必须修改文件与提交顺序

1. P3.1：`VERSION`、Python input/lock、三个Dockerfile、Flyway Dockerfile、Maven native排除、基础镜像清单。
2. P3.2：`compose.prod.yaml`和entrypoint的只读根/capability/tmpfs适配及测试。
3. P3.3：`docker-bake.hcl`、多架构builder检查、目标/标签测试。
4. P3.4：在线发布、SBOM、digest、漏洞与Secret门禁。
5. P3.5：离线包、preflight/install/upgrade/rollback和allowlist扫描。
6. P3.6：Windows amd64构建、离线安装、健康/smoke、备份恢复和P3实施报告。

## 11. 外部依据

- Docker multi-platform build与QEMU/native builder区别：https://docs.docker.com/build/building/multi-platform/
- Docker BuildKit SBOM/provenance：https://docs.docker.com/build/metadata/attestations/
- Python official image slim与编译依赖说明：https://hub.docker.com/_/python
- Docker Official Images架构清单：https://github.com/docker-library/official-images
- PyPI当前wheel元数据：https://pypi.org/
- Flyway Docker与自定义镜像要求：https://documentation.red-gate.com/fd/flyway-docker-321585710.html

所有公开清单结论只代表审计日期；发布通过version+digest固定，不依赖本文长期追踪浮动标签。
