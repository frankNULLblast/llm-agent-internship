#!/usr/bin/env bash
# 从 RabbitMQ 侧验证队列属性（教材 Day 3 步骤 4）。
set -euo pipefail

podman exec agent-rabbit \
  rabbitmqctl list_queues -p agent_lab \
  name durable messages_ready messages_unacknowledged consumers
