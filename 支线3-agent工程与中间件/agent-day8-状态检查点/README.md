# Agent Backend Day 8：PostgreSQL Checkpoint、Celery 执行与人工恢复

## 今天做了什么

把内存图接到 PostgreSQL checkpointer，并用两类 Celery 任务（`agent.execute` / `agent.resume`）分别执行与恢复。Worker 到达人工节点后退出当前任务；API、Worker 重启后仍能使用原 `run_id/thread_id` 恢复。

> ⚠️ **可运行代码位置说明（重要）**
> 当天代码在培训 VM（Red Hat 8，`192.168.172.100`）真实跑通，是 `patent-agent-service`
> （Day 3 提交 `e13000b` 之上的演进）的一部分。**本仓库仅保留教材对应的设计与配置**，
> 未含 VM 实跑代码与输出，不伪造实跑日志。同目录 `tasks.py` 是教材 Day 8 的最终完整版本，
> `ops/init_checkpoints.py` 与 `tests/fake_model.py` 为配套脚本。

## 关键技术点

- **应用表和 checkpoint 表由不同工具管理**：Alembic 只管 `agent_runs`/`agent_run_events`；`PostgresSaver.setup()` 只初始化 LangGraph checkpoint 表；二者用同一 PostgreSQL 实例但职责分开，Alembic migration 不复制框架内部表结构。
- **等待人工时没有 Celery 任务占着进程**：首次任务运行到 `interrupt()` 后，checkpoint 写入 PG、`agent_runs.status` 写为 `waiting_review`、本次 Celery 任务结束并 ACK；人工提交后 API 投递新 resume task，以同一 `thread_id` 恢复。这比在 Worker 中 `sleep`/轮询几小时更可靠。
- **两套持久状态用途不同**：`agent_runs` 是对外业务状态和审计入口；checkpoint 是图内部恢复数据。API 不直接读框架表，checkpoint 也不当业务查询表。
- **有限重试**：`retry_or_fail()` 是唯一入口，最多 3 次尝试（延迟 2、4 秒），真实模型 SDK 自身不再重试（Day 7 已设 `max_retries=0`），避免重试相乘。错误正文不写入业务表。
- **URL 方案不同**：`SQLALCHEMY_DATABASE_URL=postgresql+psycopg://...`（SQLAlchemy）；`LANGGRAPH_DATABASE_URL=postgresql://...`（PostgresSaver，不用 `+psycopg`）。

## 关键代码与配置

见同目录：

- `tasks.py`：最终完整版——celery 配置、`TRANSIENT_ERRORS`、`claim_task`/`save_waiting_review`/`save_terminal`/`save_failed`/`retry_or_fail`，以及 `execute_agent_run`（首次）、`resume_agent_run`（恢复）、`publish_execute`/`publish_resume`。Day 3/4 探针与 Day 5 临时任务已删除，只剩 `agent.execute` 与 `agent.resume`。
- `ops/init_checkpoints.py`：`PostgresSaver.from_conn_string(LANGGRAPH_DATABASE_URL).setup()`，可重复执行。
- `tests/fake_model.py`：固定 fake extractor（含 `[PRIORITY_REVIEW]`/`[MODEL_TIMEOUT]`/`[BAD_MODEL_OUTPUT]`/`[MODEL_429]`/`[MODEL_DELAY_15]` 开关），无网络、无随机数；`AGENT_EXTRACTOR_MODE=fake` 时由 Worker 使用。
- `tests/__init__.py`：空包标记。

## 与教材对应章节

教材《大模型与智能体 Agent 工程与中间件两周实习教程》→ `## Agent Backend Day 8：PostgreSQL Checkpoint、Celery 执行与人工恢复`（约第 4442–5339 行）。

## 结果或验证方式（在 VM 上执行）

1. `python ops/init_checkpoints.py` 后可同时看到应用表与 `checkpoint%` 框架表；重复运行仍成功。
2. 用 `AGENT_EXTRACTOR_MODE=fake` 启动两个 Worker 与 API，创建 run，轮询到 `waiting_review`；`celery inspect active` 两个节点 active 为空（Worker 已释放执行槽）；`checkpoints` 表中 `thread_id` == `run_id`。
3. `Ctrl+C` 停止 API 与两个 Worker（不停止 PG），重启后状态仍 `waiting_review`；提交 approve → 轮询到 `succeeded`，结果含 decision/原票据复核/原费用汇总/fake usage。
4. 新幂等键创建 + reject → 终态 `rejected`（不是 `failed`）。
5. 跨进程 ID 核对：创建 request_id、首次 task_id、`task_started → graph_waiting_review`、人工 request_id、resume task_id、`task_started → run_terminal`；task_id 可变，run_id 不变。
6. **故障演练（本日必做）**：首次到达 `waiting_review` → 全部进程退出 → PG 保留 checkpoint/状态 → 进程重启 → 同一 run 提交人工决定 → 新 Celery 任务恢复并完成。

> 本仓库不保存上述输出；验证需在培训 VM 的 `patent-agent-service` 按教材步骤进行。
