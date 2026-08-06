#!/usr/bin/env bash
# Agent-Day1：一次性创建隔离实验拓扑。
# 前提：已在 patent-agent-service 目录下 `set -a; source .env; set +a`。
# 只创建，不删除；重复执行前先确认容器/网络/卷是否已存在。
set -euo pipefail

: "${AGENT_PG_PASSWORD:?未加载 .env}"
: "${AGENT_REDIS_PASSWORD:?未加载 .env}"
: "${AGENT_RABBIT_PASSWORD:?未加载 .env}"

# 1. 固定标签镜像，不使用 latest
podman pull docker.io/library/postgres:17.10-alpine
podman pull docker.io/library/redis:8.8.1-alpine
podman pull docker.io/library/rabbitmq:4.3.3-management
podman image inspect \
  docker.io/library/postgres:17.10-alpine \
  docker.io/library/redis:8.8.1-alpine \
  docker.io/library/rabbitmq:4.3.3-management \
  --format '{{.RepoTags}} {{.Digest}}'

# 2. 专用网络与两个持久卷；Redis 只保存可重建缓存，故意不建卷
podman network create agent-lab-net
podman volume create agent-pg-data
podman volume create agent-rabbit-data

# 3. PostgreSQL：唯一事实源
podman run --detach \
  --name agent-pg \
  --hostname agent-pg \
  --network agent-lab-net \
  --publish 127.0.0.1:5432:5432 \
  --env POSTGRES_DB=agent_lab \
  --env POSTGRES_USER=agent_app \
  --env "POSTGRES_PASSWORD=$AGENT_PG_PASSWORD" \
  --volume agent-pg-data:/var/lib/postgresql/data:Z \
  --health-cmd 'pg_isready --quiet --username="$POSTGRES_USER" --dbname="$POSTGRES_DB"' \
  --health-interval 10s \
  --health-timeout 5s \
  --health-retries 12 \
  --health-start-period 30s \
  docker.io/library/postgres:17.10-alpine

# 4. Redis：无持久化，128MB 上限，allkeys-lru
#    密码经 REDISCLI_AUTH 传递，避免出现在 redis-cli -a 的进程参数里
podman run --detach \
  --name agent-redis \
  --hostname agent-redis \
  --network agent-lab-net \
  --publish 127.0.0.1:6379:6379 \
  --env "REDIS_PASSWORD=$AGENT_REDIS_PASSWORD" \
  --health-cmd 'REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli ping' \
  --health-interval 10s \
  --health-timeout 5s \
  --health-retries 12 \
  --health-start-period 20s \
  docker.io/library/redis:8.8.1-alpine \
  sh -c 'exec redis-server --save "" --appendonly no --maxmemory 128mb --maxmemory-policy allkeys-lru --requirepass "$REDIS_PASSWORD"'

# 5. RabbitMQ：固定 hostname，否则重建后无法复用旧卷
podman run --detach \
  --name agent-rabbit \
  --hostname agent-rabbit \
  --network agent-lab-net \
  --publish 127.0.0.1:5673:5672 \
  --env RABBITMQ_DEFAULT_USER=agent_worker \
  --env "RABBITMQ_DEFAULT_PASS=$AGENT_RABBIT_PASSWORD" \
  --env RABBITMQ_DEFAULT_VHOST=agent_lab \
  --volume agent-rabbit-data:/var/lib/rabbitmq:Z \
  --health-cmd 'rabbitmq-diagnostics -q ping' \
  --health-interval 30s \
  --health-timeout 5s \
  --health-retries 12 \
  --health-start-period 60s \
  docker.io/library/rabbitmq:4.3.3-management

# 6. 有界等待健康：最多 45 轮 × 2 秒
for attempt in $(seq 1 45); do
  all_healthy=true
  for name in agent-pg agent-redis agent-rabbit; do
    status=$(podman inspect "$name" --format '{{.State.Health.Status}}')
    printf '%s status=%s attempt=%s\n' "$name" "$status" "$attempt"
    if [ "$status" != healthy ]; then
      all_healthy=false
    fi
  done
  if [ "$all_healthy" = true ]; then
    break
  fi
  sleep 2
done

for name in agent-pg agent-redis agent-rabbit; do
  test "$(podman inspect "$name" --format '{{.State.Health.Status}}')" = healthy
done

printf 'agent lab containers created and healthy\n'
