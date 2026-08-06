#!/usr/bin/env bash
# Day 3 步骤 7-8：构建 localhost/linux-lab-web:0.1 并以 rootless Podman 运行
# 对应教材：Linux Day 3 → 分步操作 → 7. 创建完整 Web 镜像源文件 / 8. 构建并运行 Web 容器
#
# 前提：本目录的 web/Containerfile 与 web/index.html 已放到 ~/linux-lab/web/ 下。
set -Eeuo pipefail

export LC_ALL=C

LAB_DIR="$HOME/linux-lab"
IMAGE='localhost/linux-lab-web:0.1'
BASE_IMAGE='docker.io/library/nginx:1.30.4-alpine'
CONTAINER='linux-lab-web'

cd "$LAB_DIR"

echo '== build =='
# 先显式拉固定版本基础镜像，再用 --pull=never 构建，保证用的就是这一份
podman pull "$BASE_IMAGE"
podman build --pull=never \
  --tag "$IMAGE" \
  --file web/Containerfile web
podman images
podman image inspect "$IMAGE" --format 'id={{.Id}} tags={{.RepoTags}}'

echo '== firewall: persistent 8080 =='
DEFAULT_IF="$(ip -4 route show default | awk 'NR == 1 {print $5}')"
VM_IP="$(
  ip -o -4 addr show dev "$DEFAULT_IF" scope global |
    awk 'NR == 1 {split($4, address, "/"); print address[1]}'
)"
FIREWALL_ZONE="$(sudo firewall-cmd --get-zone-of-interface="$DEFAULT_IF")"
test "$FIREWALL_ZONE" != 'no zone'
sudo firewall-cmd --permanent --zone="$FIREWALL_ZONE" --add-port=8080/tcp
sudo firewall-cmd --reload
sudo firewall-cmd --zone="$FIREWALL_ZONE" --query-port=8080/tcp

echo '== run =='
# publish 格式是 宿主机地址:宿主机端口:容器端口
if podman container exists "$CONTAINER"; then
  echo "STOP: container $CONTAINER already exists; inspect it before continuing" >&2
  exit 1
fi
podman run --detach \
  --name "$CONTAINER" \
  --publish "${VM_IP}:8080:80" \
  "$IMAGE"
podman ps
podman port "$CONTAINER"
podman logs "$CONTAINER"

echo '== verify =='
curl --fail --show-error "http://${VM_IP}:8080/" | grep 'Linux Lab Web 0.1'
podman exec "$CONTAINER" nginx -v
podman exec "$CONTAINER" cat /usr/share/nginx/html/index.html
# HEALTHCHECK 每 10s 跑一次，等 10-20 秒后 health 应变成 healthy
podman inspect "$CONTAINER" \
  --format 'status={{.State.Status}} health={{if .State.Health}}{{.State.Health.Status}}{{else}}not-configured{{end}}'

cat <<NOTE

Windows PowerShell 7 侧验证：
  \$VmIp = '$VM_IP'
  Test-NetConnection -ComputerName \$VmIp -Port 8080
  (Invoke-WebRequest -Uri "http://\${VmIp}:8080/" -UseBasicParsing).Content

端口被占用时先定位，不要随意结束未知进程：
  ss -lntp '( sport = :8080 )'
  sudo lsof -nP -iTCP:8080 -sTCP:LISTEN
  podman ps --format '{{.Names}}\t{{.Ports}}'
NOTE
