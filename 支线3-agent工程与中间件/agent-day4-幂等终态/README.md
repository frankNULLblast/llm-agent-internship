# Agent Backend Day 4：双 Worker、late ACK 与幂等终态

## 今天做了什么

启动两个同构 Worker，验证并行消费、Worker 执行进程丢失后的重新投递（接管），以及重复执行最多只形成一份 PostgreSQL 终态。

> ⚠️ **可运行代码位置说明（重要）**
> 当天代码在培训 VM（Red Hat 8，`192.168.172.100`）真实跑通，是 `patent-agent-service`
> （Day 3 提交 `e13000b` 之上的后续演进）的一部分。**本仓库仅保留教材对应的设计与配置**，
> 未含 VM 实跑代码与输出，不伪造实跑日志。同目录 `tasks.py` 是教材 Day 4 在 Day 3 基础上
> 增加的 `slow_probe_run` 设计骨架。

## 关键技术点

- **late ACK 把失败窗口移到任务执行之后**：`task_acks_late=True` 表示 Worker 成功执行后才确认消息；若进程中途丢失，`task_reject_on_worker_lost=True` 允许 broker 把未确认消息交给另一个 Worker。代价是任务可能执行多次——网络故障、Worker 崩溃、ACK 丢失都可能造成重投，因此不能承诺 exactly once。
- **幂等不等于「不重复执行」**：允许同一个模型调用在极端情况下重复发生，但不允许产生两个业务终态。保护手段：
  1. API 先分配固定 Celery `task_id` 并写入 `current_task_id`；
  2. Worker 只接受与当前任务 ID 匹配的消息；
  3. 最终写入时锁定 `agent_runs` 行（`SELECT ... FOR UPDATE`）；
  4. 若行已是终态，只记 `duplicate_terminal_skipped` 事件，不覆盖结果。
- **`prefetch=1` 使演练可观察**：两个 Worker 各并发 1、prefetch 1 时，两个慢任务会分别被领取。这是本课程最容易观察的配置，不是吞吐调优结论。

## 关键代码与配置

见同目录：

- `tasks.py`：保留 Day 3 配置与 `probe`，新增 `slow_probe_run`（`bind=True, max_retries=0`）。`sleep` 参数从 PostgreSQL 请求数据读取，任务消息仍只有 `run_id`/`request_id`。
- `ops/start_two_workers.sh`：终端 A/B 各启动一个同构 Worker（`worker1@%h` / `worker2@%h`，concurrency=1，prefetch=1）。

## 与教材对应章节

教材《大模型与智能体 Agent 工程与中间件两周实习教程》→ `## Agent Backend Day 4：双 Worker、late ACK 与幂等终态`（约第 1781–2205 行）。

## 结果或验证方式（在 VM 上执行）

1. **并行**：两个 `probe_seconds=12` 任务，由两个不同 Worker 各自领取；PG 查询两行均 `succeeded`，且每行只有一个 `result_json`。
2. **接管**：发布 `probe_seconds=30`，进入 `running` 后，只读确认 `ps -eo pid,ppid,stat,args | grep '[c]elery.*worker'` 的子进程 PID，仅 `kill -9` 该子进程（不用 `pkill -9 celery`，不杀容器/SSH/DB）。`list_queues` 显示消息被重新投递，由可用 Worker 完成。`agent_runs` 最终只有一份 `succeeded`；事件可多次出现 `probe_started`（至少一次交付的可见证据）。
3. **重复投递**：对已成功的 run，用**原 task ID** 再发布一次；业务结果不变，新增 `duplicate_or_stale_task_skipped` 或 `duplicate_terminal_skipped` 事件。

固定测试输入：并行两个 `12`；接管一个 `30`；重复投递复用成功任务的原 `run_id`/`request_id`/task ID。

> 本仓库不保存上述输出；验证需在培训 VM 的 `patent-agent-service` 按教材步骤进行。
