# Agent Backend Day 6：Redis 终态 cache-aside 与降级

## 今天做了什么

只为「不可再变化的终态」查询加 Redis cache-aside。Redis 被清空或停机时，API 仍从 PostgreSQL 返回正确结果；`/ready` 保持 `200` 并标记 `redis: degraded`。

> ⚠️ **可运行代码位置说明（重要）**
> 当天代码在培训 VM（Red Hat 8，`192.168.172.100`）真实跑通，是 `patent-agent-service`
> （Day 3 提交 `e13000b` 之上的演进）的一部分。**本仓库仅保留教材对应的设计与配置**，
> 未含 VM 实跑代码与输出，不伪造实跑日志。同目录 `cache.py` 与 `tests/test_cache.py`
> 是教材 Day 6 的片段与测试，需合并进工程后运行。

## 关键技术点

- **cache-aside 固定流程**：`GET 终态` → Redis 命中则直接返回；未命中/故障则读 PG，若是终态则尽力写 Redis（TTL 300 秒）。
- **只缓存终态**：`queued/running/waiting_review/enqueue_failed` 都会变化，不缓存；`succeeded/rejected/failed` 不再变化，缓存完整且安全的 API 视图。
- **Redis 丢失不能造成业务丢失**：Redis 无持久卷，允许重启后为空。PostgreSQL 是唯一事实源；删除 key / `FLUSHDB` / 停止 Redis 都不能改变业务结果。
- **缓存失败是降级，不是 500**：读缓存失败继续读 PG；写缓存失败仍返回 PG 结果。只记录 `cache_get_failed/cache_set_failed` 和 run ID，不记录结果正文。

## 关键代码与配置

见同目录：

- `cache.py`：`CACHE_TTL_SECONDS=300`、`cache_key()`、`redis_client()`（lru_cache，decode_responses）、`read_terminal_cache()`、`write_terminal_cache()`、`delete_terminal_cache()`。无自定义缓存类、后台刷新、锁或失效广播。
- `main_cache.py`：对 `main.py` 中 `read_agent_run()` 的 cache-aside 替换（只替换函数体）。
- `tests/test_cache.py`：三个集成测试（只缓存终态 / TTL 有界 / 损坏缓存值被丢弃）+ 一个 API 测试（损坏缓存回退 PG）。

## 与教材对应章节

教材《大模型与智能体 Agent 工程与中间件两周实习教程》→ `## Agent Backend Day 6：Redis 终态 cache-aside 与降级`（约第 3431–3929 行）。

## 结果或验证方式（在 VM 上执行）

1. 用固定终态样例建一条 `succeeded` run，首次 `GET` 写入缓存；`redis-cli EXISTS agent:run:{run_id}`=`1`，`TTL` 在 `1..300`；二次 `GET` 命中相同业务 JSON。
2. 建一条 `waiting_review` run，`GET` 后 `EXISTS`=`0`（非终态不入缓存）。
3. **故障演练**：`DEL` 该缓存 key → `GET` 仍从 PG 得到相同结果并重新生成 key；`podman stop agent-redis` → `GET` 仍 `200` 且正文与 PG 一致，`/ready` 仍 `200` 且 `checks.redis=degraded`，日志只含缓存失败事件与 run ID，无 URL/密码/结果正文；`podman start agent-redis` 后无需重启 API 即可恢复。

> 本仓库不保存上述输出；验证需在培训 VM 的 `patent-agent-service` 按教材步骤进行。
