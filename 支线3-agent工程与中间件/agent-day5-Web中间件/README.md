# Agent Backend Day 5：Web 中间件、异步接口与幂等创建

## 今天做了什么

让 FastAPI 只做「校验、持久化、投递」，不直接运行 Agent。完成：请求 ID/耗时中间件、三个 Agent 接口、安全日志、以及 `/ready` 健康检查，并验证 `202/404/409/422/503` 契约。

> **可运行代码位置说明（重要）**
> 当天代码在培训 VM（Red Hat 8，`192.168.172.100`）的 `patent-agent-service`（Day 3 提交 `e13000b` 之上的演进）里真实跑通。
> **本仓库保留的是教材对应的设计片段**，需合并进 VM 上的 `main.py` / `storage.py` / `tasks.py` 才能运行，
> 单独拿本目录的文件是跑不起来的。VM 上的落地方式：`storage.py` 追加 6 个 run 函数、
> `tasks.py` 追加 `publish_execute` / `publish_resume`、新增 `agent_day5.py` 模块、`main.py` 末尾 `import agent_day5`。
> 实跑结果见下方「结果或验证方式」，输出为 VM 真实执行所得，未伪造。

## 关键技术点

- **`202 Accepted` 不是处理成功**：创建接口完成「边界校验 + run 已存 PG + 消息已被 RabbitMQ 接受」三件事后返回 `202`；Agent 尚未产出结果，客户端随后用 `GET` 查询状态。
- **幂等键保护「创建语义」**：对规范化请求 JSON 计算 SHA-256。同一 `Idempotency-Key` + 同哈希 → 返回原 `run_id`；同 key + 不同哈希 → `409`；原状态 `enqueue_failed` 且请求相同 → 允许用新 task ID 重投。
- **中间件只记录安全元数据**：`request_id`、方法、路径、状态码、耗时；不记录 Header 全量、请求体、OCR、Cookie、密码、连接串。`request_id` 只用于关联，不参与授权。
- **broker 失败可重试**：发布失败留下 `enqueue_failed` + `broker_unavailable`，API 返回 `503` 并带可复用 `run_id`，从原 key/body 重试即可，不新建第二个 run。
- **事务边界**：`enqueue_created_run()` / `enqueue_review()` 在一条短行锁事务内完成一次 publisher-confirm 发布再提交 `queued`，不留「已提交 queued、消息却不存在」的崩溃窗口。

## 关键代码与配置

见同目录：

- `storage_runs.py`：`create_or_get_run` / `get_run` / `enqueue_created_run` / `mark_enqueue_failed` / `enqueue_review` / `record_resume_enqueue_failed`（教材 Day 5 对 `storage.py` 的扩展）。
- `main_agent.py`：教材 Day 5 对 `main.py` 的扩展——导入、`RunStatus` 等模型、安全日志中间件、`canonical_hash`/`send_execute`/`send_resume`、`/ready`、`POST /api/v1/agent-runs`、`GET .../{run_id}`、`POST .../{run_id}/review`。
- `tasks_probe_stubs.py`：Day 5 临时 `agent.execute` / `agent.resume` 任务与 `publish_execute` / `publish_resume`（Day 8 会被真实 LangGraph 执行体替换）。
- `tests/test_agent_api.py`：离线契约测试（替换 PG/Redis/publisher 边界，不消费 RabbitMQ）。

## 与教材对应章节

教材《大模型与智能体 Agent 工程与中间件两周实习教程》→ `## Agent Backend Day 5：Web 中间件、异步接口与幂等创建`（约第 2206–3430 行）。

## 结果或验证方式（在 VM 上执行）

前置：`bash ops/lab_start.sh` 起 PG / Redis / RabbitMQ 三容器，
再 `set -a; source .env; set +a` 后启动 `uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1`。
一键复现：项目根目录 `bash day5_demo.sh`（幂等，端口已占用则跳过启动，直接跑契约）。

| 场景 | 预期 | 实测 |
|---|---|---|
| `/ready` | `200`，PG / RabbitMQ / Redis 三项 ok | 已实跑通过 |
| 首次合法创建 | `202` + 新 `run_id` | 已实跑通过 |
| 同 key、同请求 | `202` + 原 `run_id` | 已实跑通过 |
| 同 key、不同请求 | `409` | 已实跑通过 |
| 缺 `Idempotency-Key` | `422` | 已实跑通过 |
| `GET` 已存在 run | `200` + 完整 run 视图 | 已实跑通过 |
| `GET` 不存在 run | `404` | 已实跑通过 |
| 错误状态提交 review | `409` | 未演练（教材场景，本次未注入） |
| RabbitMQ 不可用 | `503`，状态 `enqueue_failed` | 未演练（需故障注入，Day 7 一并做） |
| `/ready` 的 PG/Rabbit 故障 | `503`；Redis 故障仅 `degraded` | 未演练（同上） |
| `/health` | 仍是原兼容响应，版本 `0.1.0` | 已实跑通过 |

前 7 项与 `/health` 为 VM 实跑验证，输出截图见 Obsidian
`支线3-agent工程与中间件/agent-day5-Web中间件/附件/day5_验证终端.png`。
后 3 项属于故障注入场景，本次未演练，不列为已完成。
