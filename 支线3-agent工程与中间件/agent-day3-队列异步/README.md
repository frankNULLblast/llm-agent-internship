# Agent Backend Day 3：RabbitMQ 与单队列 Celery

## 今天做了什么

把「HTTP 请求」与「耗时任务」真正分离。完成后：RabbitMQ 中只有一个 durable queue（`agent.run`）；Celery **不配置 result backend**；确定性任务在 broker 重启后仍能继续被消费。

> ⚠️ **可运行代码位置说明（重要）**
> 当天代码在培训 VM（Red Hat 8，`192.168.172.100`）真实跑通，代码位于 VM 的
> `~/llm-agent-internship/agent-middleware-plus/patent-agent-service`，提交号 **`e13000b`**。
> **本仓库仅保留教材对应的设计与配置**，未含 VM 实跑代码与输出，不伪造实跑日志。
> 当前文件夹里的 `tasks.py` 是教材 Day 3 的设计骨架（celery 配置 + `probe` 函数签名与注释），
> 用于说明当天的队列设计与观察方法，不是用来替代 VM 上已验收的代码。

## 关键技术点

- **broker 不是结果数据库**：RabbitMQ 只负责把消息可靠交给 Worker；业务状态一律由 PostgreSQL 保存。本项目不配置 Celery result backend，也不调用 `AsyncResult.get()` / 读取 `PENDING/SUCCESS` 作为业务状态。
- **durable queue 仍不等于「绝不丢」**：队列 durable + 消息 persistent + 发布者确认 + 消费者 ACK 是一组配合机制，但网络断开时仍可能出现「发布方不知道消息是否被接收」的歧义。最终按 **「至少一次 + 幂等写入」** 设计。
- **任务消息保持小而稳定**：业务任务只传 `run_id` 和 `request_id`；OCR、费用、结果都从 PostgreSQL 读取，避免大消息、隐私复制和重试时参数漂移。

### Celery 关键配置（来自教材 Day 3）

| 配置项 | 值 | 含义 |
|---|---|---|
| `task_default_queue` | `agent.run` | 唯一业务队列 |
| `task_queues` | `Queue("agent.run", durable=True)` | 持久队列 |
| `task_default_delivery_mode` | `2` | 消息持久化 |
| `task_ignore_result` | `True` | 不依赖 result backend |
| `task_acks_late` | `True` | 执行成功后才 ACK（Day 4 接管的基础） |
| `task_reject_on_worker_lost` | `True` | Worker 丢失后 broker 可重投 |
| `worker_prefetch_multiplier` | `1` | 每 Worker 每次只预取一个 |
| `broker_transport_options` | `{"confirm_publish": True}` | 发布者确认 |
| `task_publish_retry` | `False` | 由 API 显式处理投递失败 |

## 关键代码与配置

见同目录：

- `tasks.py`：教材 Day 3 的 celery 应用配置与 `agent.probe` 任务骨架（设计参考）。
- `ops/start_worker.sh`：启动单个 Worker 的脚本（对应教材终端 A）。
- `ops/publish_probe.sh`：从另一个终端发布确定性任务。
- `ops/verify_queue.sh`：从 RabbitMQ 侧验证队列属性（durable / ready / consumers）。
- `rabbitmq-setup.md`：vhost `agent_lab`、用户与权限的创建说明。

## RabbitMQ 配置要点

- 使用独立 vhost `agent_lab`，不混用默认 vhost。
- AMQP 只从宿主机 `127.0.0.1:5673` 访问（容器映射端口）。
- 不安装 Flower；本课程规模下 `rabbitmqctl`、结构化日志和 PostgreSQL 已足够。

## 与教材对应章节

教材《大模型与智能体 Agent 工程与中间件两周实习教程》→ `## Agent Backend Day 3：RabbitMQ 与单队列 Celery`（约第 1531–1780 行）。

## 结果或验证方式（在 VM 上执行）

1. 启动一个 Worker，横幅显示：transport 指向 RabbitMQ、results disabled、concurrency=1、queue 仅 `agent.run`、注册任务仅 `agent.probe`。
2. 发布 `agent.probe --args='[21]'`，Worker 日志出现：
   `{"event":"probe_completed","value":21,"doubled":42,"worker":"..."}`
3. `rabbitmqctl list_queues -p agent_lab name durable messages_ready messages_unacknowledged consumers` → `agent.run` 的 `durable=true`。
4. **故障演练**：`Ctrl+C` 停 Worker 后发布 `args='[22]'`；重启 RabbitMQ（`podman restart agent-rabbit`）并等待 healthy；`list_queues` 显示仍有 1 条 ready、0 消费者。重启 Worker 后日志出现 `value=22`、`doubled=44`。这是「停机时已进 broker 的持久消息」测试，不是断言所有网络边界恰好一次。

固定测试输入：在线消费整数 `21`；Worker 离线且 RabbitMQ 重启整数 `22`；队列名固定 `agent.run`。

> 本仓库不保存上述输出。验证需在培训 VM（commit `e13000b`）按教材步骤进行。
