#!/usr/bin/env bash
# lab_start.sh — 启动 Agent 中间件实验室（rootless podman @ Anolis 8 / SELinux Enforcing）
# 放置于 patent-agent-service/ops/ 下，在项目根目录或 ops/ 内执行均可。
# 设计目标：幂等、自愈。容器已存在则直接 start；不存在才按既定参数 create。
# 关键坑：rootless podman 下 rabbitmq 容器以 uid 999 运行，具名卷里若残留 root 属主且 0400 的
#        .erlang.cookie，entrypoint 不会覆盖它，rabbitmq 进程读不到 -> eacces 崩溃。
#        解决：create 前用 podman unshare 以 uid 999 预写 cookie，并显式传 RABBITMQ_ERLANG_COOKIE。

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENVFILE="$SCRIPT_DIR/../.env"
NET="agent-lab-net"

env_get() {
  [ -f "$ENVFILE" ] || { echo "ERROR: .env not found at $ENVFILE" >&2; exit 1; }
  grep -E "^$1=" "$ENVFILE" | head -1 | cut -d= -f2- | tr -d '\r'
}

require_keys() {
  local missing=()
  for k in AGENT_PG_PASSWORD AGENT_REDIS_PASSWORD AGENT_RABBIT_PASSWORD; do
    [ -z "$(env_get "$k")" ] && missing+=("$k")
  done
  if [ ${#missing[@]} -gt 0 ]; then
    echo "ERROR: .env 缺少密钥: ${missing[*]}" >&2
    exit 1
  fi
}

is_running() { [ "$(podman inspect -f '{{.State.Running}}' "$1" 2>/dev/null)" = "true" ]; }
exists()     { podman container exists "$1" 2>/dev/null; }

ensure_net() {
  podman network exists "$NET" || podman network create "$NET"
}

start_pg() {
  podman volume exists agent-pg-data || podman volume create agent-pg-data
  if is_running agent-pg; then echo "[pg]    already running"; return; fi
  if exists agent-pg; then echo "[pg]    starting existing"; podman start agent-pg; return; fi
  echo "[pg]    creating container"
  podman run -d --name agent-pg --network "$NET" \
    -e POSTGRES_USER=agent_app -e POSTGRES_PASSWORD="$(env_get AGENT_PG_PASSWORD)" \
    -e POSTGRES_DB=agent_lab -e PGDATA=/var/lib/postgresql/data \
    -v agent-pg-data:/var/lib/postgresql/data:Z \
    -p 127.0.0.1:5432:5432 \
    docker.io/library/postgres:17.10-alpine
}

start_redis() {
  if is_running agent-redis; then echo "[redis] already running"; return; fi
  if exists agent-redis; then echo "[redis] starting existing"; podman start agent-redis; return; fi
  echo "[redis] creating container"
  podman run -d --name agent-redis --network "$NET" \
    -e REDIS_PASSWORD="$(env_get AGENT_REDIS_PASSWORD)" \
    -p 127.0.0.1:6379:6379 \
    docker.io/library/redis:8.8.1-alpine \
    sh -c 'exec redis-server --save "" --appendonly no --maxmemory 128mb --maxmemory-policy allkeys-lru --requirepass "$REDIS_PASSWORD"'
}

start_rabbit() {
  podman volume exists agent-rabbit-data || podman volume create agent-rabbit-data
  if is_running agent-rabbit; then echo "[rabbit] already running"; return; fi
  if exists agent-rabbit; then echo "[rabbit] starting existing"; podman start agent-rabbit; return; fi
  echo "[rabbit] creating container (with erlang cookie fix)"
  local VOL
  VOL="$(podman volume inspect agent-rabbit-data --format '{{.Mountpoint}}')"
  # 预写 cookie：以 rabbitmq(uid 999) 属主、0600，避免 root 属主 0400 导致的 eacces
  podman unshare bash -c "
    if [ ! -s '$VOL/.erlang.cookie' ]; then
      C=\$(python3 -c 'import secrets;print(secrets.token_hex(16))')
      printf '%s' \"\$C\" > '$VOL/.erlang.cookie'
      chown 999:999 '$VOL/.erlang.cookie'
      chmod 600 '$VOL/.erlang.cookie'
    fi"
  local COOKIE
  COOKIE="$(podman unshare cat "$VOL/.erlang.cookie")"
  podman run -d --name agent-rabbit --network "$NET" \
    -e RABBITMQ_DEFAULT_USER=agent_worker \
    -e RABBITMQ_DEFAULT_PASS="$(env_get AGENT_RABBIT_PASSWORD)" \
    -e RABBITMQ_DEFAULT_VHOST=agent_lab \
    -e RABBITMQ_ERLANG_COOKIE="$COOKIE" \
    -v agent-rabbit-data:/var/lib/rabbitmq \
    -p 127.0.0.1:5673:5672 -p 192.168.172.100:15672:15672 \
    --health-cmd "rabbitmq-diagnostics -q ping" \
    --health-interval 15s --health-timeout 5s --health-retries 5 --health-start-period 40s \
    docker.io/library/rabbitmq:4.3.3-management
}

wait_healthy() {
  local c st
  for c in agent-pg agent-redis agent-rabbit; do
    st="starting"
    for i in $(seq 1 40); do
      st="$(podman inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}nohc{{end}}' "$c" 2>/dev/null || echo down)"
      [ "$st" = "healthy" ] && break
      sleep 3
    done
    printf '  %-12s %s\n' "$c:" "$st"
  done
}

require_keys
ensure_net
start_pg
start_redis
start_rabbit
echo "=== waiting for healthy (有界等待，最长 ~120s) ==="
wait_healthy
echo "=== 端口映射 ==="
podman port agent-pg agent-redis agent-rabbit 2>/dev/null
echo "done."
