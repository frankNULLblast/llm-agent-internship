#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
set -a
source .env
set +a

for name in agent-pg agent-redis agent-rabbit; do
  if ! podman container exists "$name"; then
    printf 'missing container: %s\n' "$name" >&2
    exit 1
  fi
done

podman start agent-pg agent-redis agent-rabbit >/dev/null

for attempt in $(seq 1 45); do
  pending=0
  for name in agent-pg agent-redis agent-rabbit; do
    status=$(podman inspect "$name" --format '{{.State.Health.Status}}')
    printf '%s status=%s attempt=%s\n' "$name" "$status" "$attempt"
    if [ "$status" != healthy ]; then
      pending=1
    fi
  done
  if [ "$pending" -eq 0 ]; then
    printf 'agent lab infrastructure is healthy\n'
    exit 0
  fi
  sleep 2
done

printf 'infrastructure did not become healthy\n' >&2
exit 1
