# Agent-Day1 基线拓扑

对应教材：《大模型、智能体学习 plus（agent工程与中间件）》→ `Agent Backend Day 1：基线、隔离拓扑与三个基础服务`。

## 这天做了什么

在续篇仓库 `patent-agent-service` 上建立十天实验的基线：

1. 用固定版本号替换 `requirements.txt`，不用 `pip freeze`；
2. 补齐 `.gitignore`、新建 `.env.example`，并在本地生成不落盘到 Git 的 `.env`；
3. 拉取三个固定标签镜像，创建专用网络与两个命名卷；
4. 用 rootless Podman 起 PostgreSQL、Redis、RabbitMQ 三个容器，全部只绑定 `127.0.0.1`；
5. 写 `ops/lab_start.sh` / `ops/lab_stop.sh`，用**有界轮询**等健康，不用固定 `sleep`；
6. 做一次「停 Redis → 用启动脚本恢复」的故障演练。

## 关键技术点

### 三类存储的定位差异

| 组件 | 数据消失后的后果 | 本教程策略 |
|---|---|---|
| PostgreSQL | 任务、结果和人工决定丢失 | 命名卷 `agent-pg-data`，Day 10 做备份恢复 |
| Redis | 第一次查询变慢 | 不持久化，自动从 PostgreSQL 重建，**不建卷** |
| RabbitMQ | 尚未消费的任务丢失 | durable queue + persistent message + 命名卷 `agent-rabbit-data` |

事实优先级固定为：
`PostgreSQL 任务表 > LangGraph checkpoint > RabbitMQ 投递状态 > Redis 缓存`。

### 容器健康 ≠ 业务就绪

- `pg_isready` 只表示服务器接受连接，不表示 Alembic 已升级；
- Redis `PING` 只表示缓存可连接，不表示某个 key 存在；
- `rabbitmq-diagnostics ping` 只表示节点存活，不表示 Celery task 已注册。

真正的依赖组合检查要到 Day 5 的 `/ready` 才出现。

### 密码生成与不落盘

用 `secrets.token_urlsafe(24)` 生成只含 URL 安全字符的密码，直接重定向进 `.env`，
`chmod 600`，并 `unset` 掉 shell 变量。全程不执行 `env`、`set` 或 `echo "$SQLALCHEMY_DATABASE_URL"`。
手写含 `@` `:` `/` 的密码会让 SQLAlchemy / AMQP URL 解析失败。

### 有界等待健康检查

`ops/lab_start.sh` 最多轮询 45 次、每次间隔 2 秒，全部 `healthy` 才退出 0；
超时退出 1。不使用 `sleep 5` 猜测启动完成。

## 关键代码或配置

| 文件 | 作用 |
|---|---|
| `requirements.txt` | 固定 14 个直接依赖的完整版本 |
| `.env.example` | 只含占位符的配置样例，可提交 |
| `gitignore.example` | Day 1 要求 `.gitignore` 至少包含的条目（此处改名保存，避免影响本仓库 Git 行为） |
| `ops/create_containers.sh` | 拉镜像、建网络与卷、创建三个容器、有界等待健康 |
| `ops/lab_start.sh` | 每日启动：只 start 三个精确容器并等健康 |
| `ops/lab_stop.sh` | 逆序停止三个容器，`--time 30` |

固定拓扑与端口：

```text
├─ 127.0.0.1:8000  FastAPI（宿主机 Python，1 进程）
└─ rootless Podman
   ├─ agent-pg       127.0.0.1:5432   卷 agent-pg-data
   ├─ agent-redis    127.0.0.1:6379   无卷
   └─ agent-rabbit   127.0.0.1:5673 → 容器 5672   卷 agent-rabbit-data
```

不开放新的 firewalld 端口，不使用 `0.0.0.0`、host network 或 privileged 容器。

## 结果与验证方式

本机（Windows）没有 Podman 与这三个容器，以下为**预期行为与验证命令**：

```bash
# 1. 三个容器都 healthy
for name in agent-pg agent-redis agent-rabbit; do
  podman inspect "$name" --format '{{.State.Health.Status}}'
done      # 预期三行都是 healthy

# 2. 只绑定回环地址
ss -lntp | grep -E '127\.0\.0\.1:(5432|6379|5673)'

# 3. 只有 PG 和 Rabbit 有命名卷
podman inspect agent-redis --format '{{range .Mounts}}{{println .Name}}{{end}}'   # 预期无输出

# 4. .env 权限与未被跟踪
stat -c '%a %n' .env      # 预期 600 .env
git status --short        # 预期不出现 .env

# 5. 故障演练：停 Redis 后用启动脚本恢复
podman stop --time 30 agent-redis
./ops/lab_start.sh
podman healthcheck run agent-redis    # 预期退出码 0
```

验收清单（教材原文）：依赖版本一致、镜像用完整名称与固定标签、三服务健康且只监听回环、
Redis 无持久卷、启停脚本只操作三个精确容器、Redis 停后能恢复、未记录或提交密码。

提交信息：`agent backend day 1: add isolated middleware lab`
