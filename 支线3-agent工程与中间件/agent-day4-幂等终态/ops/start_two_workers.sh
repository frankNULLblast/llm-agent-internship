#!/usr/bin/env bash
# 启动两个同构 Worker（教材 Day 4 终端 A 与 B）。
# 真实运行在培训 VM 的 patent-agent-service。
# 用法：
#   ./ops/start_two_workers.sh 1   # worker1@%h
#   ./ops/start_two_workers.sh 2   # worker2@%h
set -euo pipefail

INDEX="${1:?请传入 1 或 2}"

cd "$HOME/llm-agent-internship/agent-middleware-plus/patent-agent-service"
source .venv/bin/activate
set -a
source .env
set +a

celery -A tasks.celery_app worker \
  --loglevel=INFO \
  --concurrency=1 \
  --hostname="worker${INDEX}@%h" \
  --queues='agent.run'
