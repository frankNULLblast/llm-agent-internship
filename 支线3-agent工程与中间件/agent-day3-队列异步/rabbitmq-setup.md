# RabbitMQ 配置要点（Day 3）

## vhost 与用户

- 使用独立 vhost `agent_lab`，不混用默认 vhost `/`。
- 为应用创建专用用户（如 `agent_app`），仅授予 `agent_lab` 的 configure/write/read 权限。
- 应用通过 `CELERY_BROKER_URL=amqp://agent_app:<password>@127.0.0.1:5673/agent_lab` 连接。

## 访问边界

- AMQP 只从宿主机 `127.0.0.1:5673` 访问（容器端口映射），不暴露到外部网络。
- 管理端口（15672）同样只绑回环，或仅本地临时查看。

## 队列声明

- 队列 `agent.run` 由 Worker 启动时声明为 `durable=True`；消息 delivery mode=2（persistent）。
- 发布端开启 `confirm_publish`，确保 broker 确认接收。
- 不安装 Flower；用 `rabbitmqctl list_queues` 与 Worker 日志观察。

## 故障演练（简述）

1. `Ctrl+C` 停止 Worker；
2. 发布一条任务（如 `args='[22]'`），`list_queues` 显示 `agent.run` 有 1 条 ready、0 消费者；
3. `podman restart agent-rabbit` 并等待 healthy；
4. 再次 `list_queues` 确认积压仍在；
5. 重启 Worker，日志出现 `value=22`、`doubled=44`。

> 真实执行与证据在培训 VM（commit e13000b）。本仓库仅保留设计配置。
