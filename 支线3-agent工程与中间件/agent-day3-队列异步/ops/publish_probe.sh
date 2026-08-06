#!/usr/bin/env bash
# 从另一个终端发布确定性 probe 任务（教材 Day 3 终端 B）。
# 用法：./ops/publish_probe.sh 21
set -euo pipefail

VALUE="${1:-21}"

cd "$HOME/llm-agent-internship/agent-middleware-plus/patent-agent-service"
source .venv/bin/activate
set -a
source .env
set +a

celery -A tasks.celery_app call agent.probe \
  --args="[$VALUE]" \
  --queue='agent.run'
