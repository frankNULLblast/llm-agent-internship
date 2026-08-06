# Linux Day 5：中间件实战

对应教材：`大模型、智能体学习 plus（linux）.md` → **Linux Day 5：MySQL、RabbitMQ 与最小综合实践**（第 3099 行起），以及第 2.3 节的固定数据流。

## 这天做了什么

用 rootless Podman 起 MySQL 8.4.10 和 RabbitMQ 4.3.3，把前四天的东西串成一条完整业务流，重点练**"先写数据库、再 ACK"**这个顺序，以及它在各种失败场景下的表现。

固定业务流（教材第 2.3 节）：

```text
send_event.py
  → RabbitMQ 持久队列 linux.events
  → consume_once.py 读取一条消息
  → MySQL 事务写入 lab_events
  → COMMIT 成功
  → RabbitMQ ACK
```

如果 MySQL 写入失败，消费者先 `ROLLBACK`，再 `NACK(requeue=True)` 把消息放回队列；**绝不能在数据库提交前 ACK**。

固定输入：

| 项目 | 固定值 |
|---|---|
| MySQL 镜像 | `docker.io/library/mysql:8.4.10` |
| RabbitMQ 镜像 | `docker.io/library/rabbitmq:4.3.3-management` |
| 网络 | `linux-lab-middleware` |
| 命名卷 | `linux-lab-mysql-data`、`linux-lab-rabbitmq-data` |
| 容器 | `mysql-lab`、`rabbitmq-lab` |
| 数据库 / 表 | `linux_lab` / `lab_events` |
| 队列 | `linux.events`（durable，消息 persistent） |
| Python 依赖 | `pika==1.4.2`、`mysql-connector-python==9.7.0` |
| 快照 | `day5-complete` |

## 端口与安全边界

| 位置 | 绑定 | 说明 |
|---|---|---|
| MySQL | `127.0.0.1:3306` | 只限虚拟机内，**不**对局域网暴露 |
| RabbitMQ AMQP | `127.0.0.1:5672` | 只限虚拟机内，**不**对局域网暴露 |
| RabbitMQ 管理页 | `<VM_IP>:15672` | 唯一需要 firewalld 放行的端口 |

因为 3306 和 5672 根本没绑到 VM 的外部地址，所以**不需要也不允许**给它们加防火墙规则。不要为了从 Windows 直连数据库就改成 `0.0.0.0`。

密码由 `openssl rand -hex 24` 随机生成，写进权限 `600` 的 `middleware/.env`，不进 Git、不进截图、不进 evidence。

## 本目录内容

| 文件 | 对应教材小节 | 作用 |
|---|---|---|
| `01-bootstrap-env.sh` | 分步操作 1–3、13 | 生成 `.env`（幂等，不覆盖）、修 `init.sql` 权限、建 venv 并装固定依赖 |
| `02-start-middleware.sh` | 分步操作 4–7 | 拉镜像、建网络与卷、起两个容器、等健康、校验端口边界 |
| `03-sql-practice.sh` | 分步操作 9 | SQL 练习：COMMIT 与 ROLLBACK 的行为对比 |
| `04-failure-drills.sh` | 分步操作 14–17 | 六个子命令覆盖空队列、坏 JSON、库失败、事务失败、正常消费、持久化 |
| `middleware/.env.example` | 分步操作 1 | 变量名与非秘密默认值，**可以**提交 |
| `middleware/init.sql` | 分步操作 3 | `lab_events` 建表语句，只读挂进容器初始化目录 |
| `middleware/requirements.txt` | 分步操作 10 | 只列直接导入的依赖并固定版本 |
| `middleware/send_event.py` | 分步操作 11 | 生产者，支持 `--malformed-test` |
| `middleware/consume_once.py` | 分步操作 12 | 消费者，支持 `--transaction-failure-test` |

实跑时把 `middleware/` 放到虚拟机的 `~/linux-lab/middleware/`。

## 关键设计点

**表结构**：`event_id` 上的唯一约束 `uq_lab_events_event_id` 让消息重复投递时不会产生重复业务记录；`payload` 用 JSON 类型，MySQL 会校验格式；`created_at` 由数据库生成。

**幂等保护**：消费者用 `INSERT ... AS new ON DUPLICATE KEY UPDATE event_id = new.event_id`。极端情况下数据库已提交但 ACK 网络失败，消息重投也不会新增行，`cursor.rowcount` 会从 `1` 变成其他值，输出 `already_present` 而不是 `inserted`。

**持久化三件套**：队列 `durable=True`、消息 `delivery_mode=2`、数据放命名卷而不是容器可写层。三者缺一，容器重建后就会丢东西。

**publisher confirms**：`channel.confirm_delivery()` 开启后，Pika 1.x 的 `basic_publish` 成功时返回 `None`，退回或 NACK 通过 `UnroutableError` / `NackError` 异常报告。

## 关键命令

加载环境（每开一个新终端都要做）：

```bash
cd "$HOME/linux-lab"
source .venv/bin/activate
set -a
source middleware/.env
set +a
```

不要执行 `env`、`set` 或 `cat middleware/.env` 并把输出存成证据。

端口边界自检：

```bash
PRIVATE_LISTENERS="$(ss -lntH | awk '{print $4}')"
grep -Fxq '127.0.0.1:3306' <<<"$PRIVATE_LISTENERS" &&
grep -Fxq '127.0.0.1:5672' <<<"$PRIVATE_LISTENERS" &&
! grep -Eq '(^0\.0\.0\.0|\[::\]):(3306|5672)$' <<<"$PRIVATE_LISTENERS"
```

只有输出 `PRIVATE PORT CHECK PASSED` 才继续。

查看队列状态：

```bash
podman exec rabbitmq-lab \
  rabbitmqctl -q list_queues name messages_ready messages_unacknowledged durable
```

## 预期结果

四个失败场景 + 正常路径，教材给出的精确检查点：

| 演练 | 命令 | 预期输出 | 退出码 | 队列 ready | `lab_events` 行数 |
|---|---|---|---|---|---|
| 空队列 | `04-failure-drills.sh empty` | `QUEUE_EMPTY` | `2` | `0` | `0` |
| 坏 JSON | `04-failure-drills.sh malformed` | `PROCESSING_FAILED: JSONDecodeError...` | `1` | `1`（NACK 重入队） | `0` |
| 数据库密码错 | `04-failure-drills.sh baddb` | MySQL 认证失败 | `1` | `1`（重新 ready） | `0` |
| 事务中途失败 | `04-failure-drills.sh txnfail` | `IntegrityError` | `1` | `1` | `0` |
| 正常消费 | `04-failure-drills.sh happy` | `{"result":"inserted",...,"acknowledged":true}` | `0` | `0` | `1` |

SQL 练习（`03-sql-practice.sh`）的精确检查：

- 回滚后 `id=1` 的 status 仍是 `new`；
- 提交后 `id=2` 的 status 是 `done`；
- 最后只保留业务表 `lab_events`，且 `SELECT COUNT(*)` 精确输出 `0`。

持久化演练（`durable`）：发一条消息不消费，停止并 `podman rm rabbitmq-lab`（**只删容器，保留命名卷**），用相同参数重建后，durable 队列和那条 persistent 消息应当还在。

"事务中途失败"这个场景最能说明问题：第一条 INSERT 已经在事务内执行了，但随后的重复键错误让**整个事务回滚**，所以数据库计数仍是 `0`，同时消息因为没有 ACK 而回到队列 —— 数据既没丢也没重复。

> 说明：本目录脚本没有在当前 Windows 机器上执行（对象是 VMware 里的 Anolis 虚拟机），因此不放输出文件。上表是教材规定的**预期行为**，不是实跑记录。

## 红线

- MySQL `3306` 与 RabbitMQ AMQP `5672` 固定绑 `127.0.0.1`，不暴露给局域网；
- 密码、`.env`、Token 不进 Git、不进截图、不进 evidence；查看密码只在未录屏的终端执行，登录后立即 `clear`；
- `purge_queue` 前必须确认队列名精确是 `linux.events` 且里面只有自己造的测试消息，不要在共享或生产 RabbitMQ 上运行；
- 教程不在 rootless `podman run` 里固定 `--memory` / `--cpus`：龙蜥 8 的 cgroup 模式和用户级 systemd delegation 可能不同，强加会让部分环境启动失败。实验总资源由 8GB 虚拟机边界控制；
- NAT DHCP 变更后不能原地改 RabbitMQ 的 host-side port mapping，要用新 IP 停止并重建 `rabbitmq-lab`，保留 `linux-lab-rabbitmq-data` 卷即可。

## 生产环境的差距

本实验的最小幂等保护够用于学习，但生产系统还应配置**重试次数**和**死信队列**，避免永久性错误的消息在队列里反复重入形成"毒消息"。这部分超出五天主线。
