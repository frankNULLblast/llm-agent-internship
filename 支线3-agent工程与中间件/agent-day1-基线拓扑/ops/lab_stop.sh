#!/usr/bin/env bash
set -euo pipefail

# 逆序停止；只按精确名称操作，禁止 podman stop -a / rm -a / volume prune
for name in agent-rabbit agent-redis agent-pg; do
  if podman container exists "$name"; then
    podman stop --time 30 "$name"
  fi
done
