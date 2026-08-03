#!/usr/bin/env bash
# lab_stop.sh — 停止（不删除）Agent 中间件实验室容器，保留数据卷与容器定义。
# 配合 lab_start.sh 使用：stop 之后 start 即可恢复，数据不丢。
# 如需彻底清理数据，手动 podman rm -f <容器> && podman volume rm <卷>。

set -uo pipefail

is_running() { [ "$(podman inspect -f '{{.State.Running}}' "$1" 2>/dev/null)" = "true" ]; }
exists()     { podman container exists "$1" 2>/dev/null; }

stop_one() {
  local c="$1"
  if ! exists "$c"; then echo "[$c] does not exist"; return; fi
  if is_running "$c"; then echo "[$c] stopping"; podman stop "$c"; else echo "[$c] not running"; fi
}

# 逆序停止：先消息队列，再缓存，最后数据库
stop_one agent-rabbit
stop_one agent-redis
stop_one agent-pg

echo "=== 容器状态 ==="
podman ps -a --filter name='^agent-(pg|redis|rabbit)$'
echo "done."
