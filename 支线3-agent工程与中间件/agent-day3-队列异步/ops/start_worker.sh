#!/usr/bin/env bash
# 启动单个 Celery Worker（教材 Day 3 终端 A）。
# 真实运行在培训 VM 的 patent-agent-service（commit e13000b）。
set -euo pipefail

cd "$HOME/llm-agent-internship/agent-middleware-plus/patent-agent-service"
source .venv/bin/activate
set -a
source .env
set +a

celery -A tasks.celery_app worker \
  --loglevel=INFO \
  --concurrency=1 \
  --hostname='worker1@%h' \
  --queues='agent.run'
