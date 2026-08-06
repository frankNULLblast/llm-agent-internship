# Agent Backend Day 9：关联日志、六条 Golden Cases 与故障矩阵

## 今天做了什么

不再增加业务功能。把 API、Worker、图节点、数据库事件串成可审计证据；自动跑六条 golden cases；逐一演练 Redis / RabbitMQ / Worker / PostgreSQL / 模型 / API 故障。所有 Worker 固定 `AGENT_EXTRACTOR_MODE=fake`，零外部调用。

> ⚠️ **可运行代码位置说明（重要）**
> 当天代码在培训 VM（Red Hat 8，`192.168.172.100`）真实跑通，是 `patent-agent-service`
> （Day 3 提交 `e13000b` 之上的演进）的一部分。**本仓库仅保留教材对应的设计与配置**，
> 未含 VM 实跑代码与输出，不伪造实跑日志。`evidence/` 不提交 Git。

## 关键技术点

- **三种 ID 构成一条证据链**：HTTP create `request_id` → `run_id/thread_id` → execute `task_id` → `waiting_review` → HTTP review `request_id` → 同一 `run_id/thread_id` → resume `task_id` → terminal。日志答「哪个进程何时做了什么」；PG 事件答「业务状态为何变化」；RabbitMQ 指标答「消息在哪里」；任何单一来源都不够。
- **指标必须有单位和边界**：只记录模型名 / prompt·completion·total token / 模型耗时 ms / Celery attempt / HTTP 耗时 ms / 最终状态与错误码；不构建监控平台，价格只在评测报告中按核验日官方页面计算。
- **故障注入要有恢复判据**：每项写清「注入前状态 / 注入动作 / 可观察失败 / 恢复动作 / 恢复后业务不变量」。

## 关键代码与配置

见同目录：

- `ops/run_golden_cases.py`：六条固定端到端用例（standard_approve / priority_approve / human_reject / structured_output_error / fee_business_error / duplicate_delivery），用真实 API+PG+Redis+RabbitMQ+两 Worker，但模型固定 fake；报告只含 case 名、run ID、终态、route、脱敏错误码、usage。
- 故障矩阵总表（见下方「结果或验证方式」）：Redis 停机、RabbitMQ 带积压重启、Worker 执行中退出、PostgreSQL 暂停、模型 timeout/429、API 独立重启、重复投递。

> 注：`tests/fake_model.py` 的 `[MODEL_429]`/`[MODEL_DELAY_15]` 故障开关在 Day 9 扩展（见 Day 8 目录），需合并进同一文件。

## 与教材对应章节

教材《大模型与智能体 Agent 工程与中间件两周实习教程》→ `## Agent Backend Day 9：关联日志、六条 Golden Cases 与故障矩阵`（约第 5341–6034 行）。

## 结果或验证方式（在 VM 上执行）

**六条 golden cases（固定输入）**

| case | 触发 | 人工动作 | 终态 |
|---|---|---|---|
| standard_approve | 标准 fake | approve | succeeded |
| priority_approve | `[PRIORITY_REVIEW]` | approve | succeeded（priority route） |
| human_reject | 标准 fake | reject | rejected |
| structured_output_error | `[BAD_MODEL_OUTPUT]` | 无 | failed |
| fee_business_error | amount=`"0.00"` | 无 | failed |
| duplicate_delivery | 终态 task 重投 | approve | succeeded 且不变 |

**故障矩阵**

| 故障 | 注入前 | 可观察失败 | 恢复动作 | 恢复后不变量 |
|---|---|---|---|---|
| Redis 停机 | 终态已在 PG | cache warning，ready degraded | 启动 Redis | GET 结果未丢 |
| RabbitMQ 带积压重启 | Worker 停、queue 有消息 | ready 消息暂不消费 | 重启 broker/Worker | 原 run 继续 |
| Worker 执行中退出 | run=running | unacked 重投 | 另一 Worker 接管 | 一份终态 |
| PostgreSQL 暂停 | run 已 queued | `/ready=503`、task retry | 尽快启动 PG | 同 run 继续 |
| 模型 timeout/429 | fake Worker 在线 | 有限 retry 事件 | 等待重试耗尽 | run=failed，错误脱敏 |
| API 独立重启 | Worker 正在执行 | HTTP 暂不可用 | 重启 API | Worker/状态不受影响 |
| 重复投递 | run 已终态 | duplicate skip 事件 | 无需修复 | 终态不变 |

证据安全扫描（grep）必须无 `DEEPSEEK_API_KEY=`、无 `AGENT_(PG|REDIS|RABBIT)_PASSWORD=`、无连接串、无完整 OCR。

> 本仓库不保存上述输出；验证需在培训 VM 的 `patent-agent-service` 按教材步骤进行。
