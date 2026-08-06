#!/usr/bin/env bash
# 教材 Day 10 的一键验收脚本（需合并进工程 ops/verify_agent_lab.sh）。
#
# ⚠️ 可运行代码位置说明：
#   当天真实跑通的代码在培训 VM 的 patent-agent-service（Day 3 提交 e13000b 之上的演进）。
#   本仓库仅保留教材对应的设计与配置，未含 VM 实跑代码与输出。
# 脚本只终止自己启动并记录 PID 的三个本地进程，不使用 pkill；
# 不删除数据库、不 purge queue、不清空 Redis。

set -euo pipefail

project_dir="$(
  CDPATH= cd -- "$(dirname -- "$0")/.." &&
    pwd
)"
cd "$project_dir"

test -f .env
test "$(stat -c '%a' .env)" = "600"
if git ls-files --error-unmatch .env >/dev/null 2>&1; then
  printf '.env must not be tracked\n' >&2
  exit 1
fi
if ! git check-ignore -q .env; then
  printf '.env must be ignored by Git\n' >&2
  exit 1
fi

set -a
source .env
set +a

./ops/lab_start.sh
queue_counts="$(
  podman exec agent-rabbit \
    rabbitmqctl list_queues -p agent_lab \
    name messages_ready messages_unacknowledged |
    awk '$1 == "agent.run" {print $2 " " $3}'
)"
case "$queue_counts" in
  ''|'0 0') ;;
  *)
    printf 'agent.run is not empty: %s\n' "$queue_counts" >&2
    printf '处理对应 run 后再执行验收；脚本不会 purge queue\n' >&2
    exit 1
    ;;
esac
alembic upgrade head
python ops/init_checkpoints.py
python -m py_compile \
  main.py \
  storage.py \
  cache.py \
  tasks.py \
  workflow.py \
  ops/init_checkpoints.py \
  ops/run_golden_cases.py
python -m pytest -q -m 'not integration'
python -m pytest -q -m integration

for port in 5432 6379 5673; do
  listeners="$(
    ss -H -ltn |
      awk -v suffix=":${port}" '$4 ~ suffix"$" {print $4}' |
      sort -u
  )"
  if [ "$listeners" != "127.0.0.1:${port}" ]; then
    printf 'port %s is not bound only on expected IPv4 loopback\n' "$port" >&2
    printf '%s\n' "$listeners" >&2
    exit 1
  fi
done

mkdir -p evidence/day10
if ss -H -ltn | awk '$4 ~ /:8000$/ {found=1} END {exit !found}'; then
  printf 'port 8000 is already in use; stop the existing API first\n' >&2
  exit 1
fi
api_pid=''
worker1_pid=''
worker2_pid=''

cleanup() {
  for pid in "$api_pid" "$worker1_pid" "$worker2_pid"; do
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
    fi
  done
  wait "$api_pid" "$worker1_pid" "$worker2_pid" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

AGENT_EXTRACTOR_MODE=fake \
celery -A tasks.celery_app worker \
  --loglevel=INFO \
  --pool=solo \
  --concurrency=1 \
  --hostname='verify1@%h' \
  --queues='agent.run' \
  >evidence/day10/worker1.log 2>&1 &
worker1_pid=$!

AGENT_EXTRACTOR_MODE=fake \
celery -A tasks.celery_app worker \
  --loglevel=INFO \
  --pool=solo \
  --concurrency=1 \
  --hostname='verify2@%h' \
  --queues='agent.run' \
  >evidence/day10/worker2.log 2>&1 &
worker2_pid=$!

uvicorn main:app \
  --host 127.0.0.1 \
  --port 8000 \
  --workers 1 \
  --no-access-log \
  >evidence/day10/api.log 2>&1 &
api_pid=$!

ready=0
for attempt in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:8000/ready |
    python -c 'import json,sys; assert json.load(sys.stdin)["status"] == "ready"'
  then
    ready=1
    break
  fi
  sleep 1
done
test "$ready" -eq 1
api_listeners="$(
  ss -H -ltn |
    awk '$4 ~ /:8000$/ {print $4}' |
    sort -u
)"
test "$api_listeners" = "127.0.0.1:8000"

health_version="$(
  curl -fsS http://127.0.0.1:8000/health |
    python -c 'import json,sys; print(json.load(sys.stdin)["version"])'
)"
test "$health_version" = "0.2.0"

GOLDEN_OUTPUT=evidence/day10/golden-results.json \
  python -m ops.run_golden_cases
if grep -R -n -E -- \
  'DEEPSEEK_API_KEY=|AGENT_(PG|REDIS|RABBIT)_PASSWORD=|(postgresql(\+psycopg)?|amqp|redis)://[^[:space:]]+:[^*@[:space:]][^@[:space:]]*@|<ocr_text>|虚构电子发票：申请号' \
  evidence/day10
then
  printf 'unsafe content found in evidence/day10\n' >&2
  exit 1
else
  scan_status=$?
  if [ "$scan_status" -ne 1 ]; then
    printf 'evidence safety scan failed, rc=%s\n' "$scan_status" >&2
    exit "$scan_status"
  fi
fi
git diff --check

printf 'verify_agent_lab: PASS\n'
