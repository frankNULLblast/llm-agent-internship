#!/usr/bin/env bash
# Day 3 步骤 9-10：只读 bind mount、命名卷、容器重建，并导出给 Day 4 用的 OCI 包
# 对应教材：Linux Day 3 → 分步操作 → 9. 只读挂载、命名卷和容器重建 / 10. 导出 OCI 镜像包
set -Eeuo pipefail

export LC_ALL=C

LAB_DIR="$HOME/linux-lab"
ANOLIS_IMAGE='registry.openanolis.cn/openanolis/anolisos:8.10'
IMAGE='localhost/linux-lab-web:0.1'
CONTAINER='linux-lab-web'
VOLUME='linux-lab-web-data'

cd "$LAB_DIR"

echo '== read-only bind mount =='
# :Z 让 Podman 给这个私有挂载打合适的 SELinux 标签，,ro 禁止容器写入
mkdir -p evidence/day03-ro
printf 'read-only-from-host\n' > evidence/day03-ro/proof.txt
podman run --rm \
  --volume "$PWD/evidence/day03-ro:/data:Z,ro" \
  "$ANOLIS_IMAGE" \
  cat /data/proof.txt

# 写入应当失败（只读文件系统），退出码非 0
if podman run --rm \
  --volume "$PWD/evidence/day03-ro:/data:Z,ro" \
  "$ANOLIS_IMAGE" \
  sh -c 'printf "should-fail\n" > /data/new.txt'; then
  echo 'STOP: write to a read-only mount unexpectedly succeeded' >&2
  exit 1
else
  echo 'expected: write to the read-only mount was rejected'
fi

echo '== named volume survives its containers =='
podman volume exists "$VOLUME" || podman volume create "$VOLUME"
podman run --rm \
  --volume "$VOLUME:/data:Z" \
  "$ANOLIS_IMAGE" \
  sh -c 'printf "named-volume-survives\n" > /data/proof.txt'
podman run --name volume-reader \
  --volume "$VOLUME:/data:Z" \
  "$ANOLIS_IMAGE" \
  cat /data/proof.txt
podman rm volume-reader
# 删掉读取容器后再读一次，两次都应输出 named-volume-survives
podman run --rm \
  --volume "$VOLUME:/data:Z" \
  "$ANOLIS_IMAGE" \
  cat /data/proof.txt
podman volume inspect "$VOLUME"

echo '== container is not the image =='
podman stop "$CONTAINER"
podman rm "$CONTAINER"
podman image exists "$IMAGE"
printf 'image_still_exists_exit_code=%s\n' "$?"

DEFAULT_IF="$(ip -4 route show default | awk 'NR == 1 {print $5}')"
VM_IP="$(
  ip -o -4 addr show dev "$DEFAULT_IF" scope global |
    awk 'NR == 1 {split($4, address, "/"); print address[1]}'
)"
podman run --detach \
  --name "$CONTAINER" \
  --publish "${VM_IP}:8080:80" \
  "$IMAGE"
curl --fail "http://${VM_IP}:8080/" | grep 'Linux Lab Web 0.1'

echo '== export the OCI archive for Day 4 =='
# .gitignore 必须先忽略 *.oci —— 包大且可重建，不进 Git
grep -n '\*.oci' .gitignore
podman save \
  --format oci-archive \
  --output web/linux-lab-web-0.1.oci \
  "$IMAGE"
ls -lh web/linux-lab-web-0.1.oci
sha256sum web/linux-lab-web-0.1.oci | tee evidence/day03-image.sha256

echo '== evidence =='
{
  echo '== address =='
  ip -br addr
  echo '== route =='
  ip route
  echo '== DNS =='
  getent hosts mirrors.openanolis.cn
  echo '== ports =='
  ss -lnt
  echo '== podman =='
  podman --version
  podman info --format 'rootless={{.Host.Security.Rootless}}'
  podman images --format '{{.Repository}}:{{.Tag}} {{.ID}}'
  echo '== SELinux =='
  getenforce
} | tee evidence/day03-network-container.txt

cat <<'NOTE'

提交：
  git add web/Containerfile web/index.html \
    evidence/day03-http/index.html \
    evidence/day03-ro/proof.txt \
    evidence/day03-image.sha256 \
    evidence/day03-network-container.txt
  git commit -m "feat: add rootless Podman web lab"

收尾（停 Web，撤掉 8080 持久规则；镜像/OCI 包/命名卷保留给 Day 4）：
  podman stop --time 10 linux-lab-web
  DEFAULT_IF="$(ip -4 route show default | awk 'NR == 1 {print $5}')"
  FIREWALL_ZONE="$(sudo firewall-cmd --get-zone-of-interface="$DEFAULT_IF")"
  sudo firewall-cmd --permanent --zone="$FIREWALL_ZONE" --remove-port=8080/tcp
  sudo firewall-cmd --reload
  sudo firewall-cmd --zone="$FIREWALL_ZONE" --query-port=8080/tcp   # 预期 no
  podman image exists localhost/linux-lab-web:0.1                   # 预期退出码 0
NOTE
