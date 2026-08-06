# Agent-Day2 数据持久化

对应教材：`Agent Backend Day 2：PostgreSQL、SQLAlchemy 与 Alembic`。

## 这天做了什么

1. 写 `storage.py`：SQLAlchemy 2.0 `DeclarativeBase` 定义 `agent_runs`、`agent_run_events` 两张表；
2. 延迟建引擎（`lru_cache` + `get_engine()`），小连接池 `pool_size=2 / max_overflow=0 / pool_pre_ping=True`；
3. `alembic init` 后完整替换 `alembic/env.py`，URL 只从进程环境读，不写进 `alembic.ini`；
4. 手写并人工审阅固定 migration `20260731_01_agent_runs.py`，`upgrade/downgrade` 对称；
5. 在**空表**状态下演练 `downgrade base → upgrade head`；
6. 加 `pytest.ini` 的 `integration` 标记，离线测试与集成测试分开跑；
7. 故障演练：临时用错误密码跑集成测试，确认报错里不出现真实密码。

## 关键技术点

### 任务表与 checkpoint 表的职责边界

- `agent_runs`：对外业务状态、输入、结果、错误码 —— API 查询它；
- `agent_run_events`：可审计的状态变化流水；
- LangGraph checkpoint 表：Day 8 才由框架 `PostgresSaver.setup()` 建，只供图恢复。

Alembic **不**管理 checkpoint 表，也不复制框架内部结构。

### 两个数据库 URL 用途不同

- `SQLALCHEMY_DATABASE_URL=postgresql+psycopg://...` —— SQLAlchemy 必须带 `+psycopg`，
  否则会去找 psycopg2；
- `LANGGRAPH_DATABASE_URL=postgresql://...` —— `PostgresSaver` 直接用 psycopg，不能带 `+psycopg`。

### 状态约束交给数据库

- `status` 用 `CHECK` 约束限定 7 个取值，写错拼写由数据库拒绝；
- `idempotency_key` 用唯一约束，并发请求即使同时「先查不到」，也只有一个 INSERT 能成功。
  Python 的先查后插只优化常见路径，**不替代**唯一约束。

### 延迟建引擎

`get_engine()` 必须延迟到首次调用，否则「导入模块就要求数据库在线」，
Day 1 之前的旧 FastAPI 与领域测试就无法离线运行。

### JSONB 与结构化列的取舍

`payload_json` / `result_json` / `model_usage` / `detail_json` 用 JSONB 存形状会演进的数据；
`status`、`idempotency_key`、`created_at` 这些要被约束、索引、排序的字段用结构化列。

## 关键代码或配置

| 文件 | 作用 |
|---|---|
| `storage.py` | 表模型、引擎/会话工厂、`session_scope()`、`add_event()`、`run_to_dict()` |
| `alembic.ini` | 只留框架配置，`sqlalchemy.url` 留空由 `env.py` 注入 |
| `alembic/env.py` | `config.set_main_option("sqlalchemy.url", database_url())`，`compare_type=True` |
| `alembic/versions/20260731_01_agent_runs.py` | 建两表两索引，downgrade 先删事件表再删运行表 |
| `pytest.ini` | 注册 `integration` 标记 |
| `tests/test_integration.py` | 三项集成测试：事务回滚、幂等键唯一、非法状态被 CHECK 拒绝 |

## 结果与验证方式

本机无 PostgreSQL 容器，以下为**预期行为与验证命令**：

```bash
alembic upgrade head
alembic current                     # 预期 20260731_01 (head)
podman exec agent-pg psql -U agent_app -d agent_lab \
  -c '\dt' -c '\d agent_runs' -c '\d agent_run_events'

# 空表回退演练
alembic downgrade base && alembic current
alembic upgrade head   && alembic current

python -m pytest -q -m 'not integration'   # 离线，不需要数据库
python -m pytest -q -m integration         # 需要 agent-pg 在线

# 故障演练：错误密码只作用于一条命令
SQLALCHEMY_DATABASE_URL='postgresql+psycopg://agent_app:wrong@127.0.0.1:5432/agent_lab' \
  python -m pytest -q -m integration
# 预期连接失败，且错误输出中不出现真实密码
```

语义检查点：migration 可空库 upgrade→downgrade→upgrade；事务异常后查不到半条记录；
相同幂等键由数据库拒绝；未知状态 `done` 由 CHECK 拒绝；旧 FastAPI/领域测试不需数据库也能跑。

提交信息：`agent backend day 2: add postgres run storage`
