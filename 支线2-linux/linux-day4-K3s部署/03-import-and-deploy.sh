#!/usr/bin/env bash
# Day 4 步骤 5-7：导入 Day 3 的 OCI 镜像 → dry-run 校验 → 部署 → 开放 NodePort 30080
# 对应教材：Linux Day 4 → 分步操作 → 5./6./7.
#
# 关键概念：Podman 与 K3s containerd 是两套独立的镜像存储。
# Podman 看得到镜像，不代表 K3s 看得到，必须通过 OCI archive 显式导入。
set -Eeuo pipefail

export LC_ALL=C

LAB_DIR="$HOME/linux-lab"
KUBECTL='/usr/local/bin/kubectl'
IMAGE_REF='localhost/linux-lab-web:0.1'
MANIFEST='k8s/web.yaml'

cd "$LAB_DIR"

echo '== step 5: import the Day 3 OCI archive into K3s containerd =='
sha256sum -c evidence/day03-image.sha256
sudo /usr/local/bin/k3s ctr images import web/linux-lab-web-0.1.oci
sudo /usr/local/bin/k3s ctr images list | grep "$IMAGE_REF"
# 用 K3s 自带的 crictl 再确认一次
sudo /usr/local/bin/k3s crictl images | grep 'localhost/linux-lab-web'

echo '== step 6: client dry-run =='
sudo "$KUBECTL" apply --dry-run=client --filename "$MANIFEST"

echo '== step 6: create the namespace idempotently =='
# server dry-run 会校验 namespaced 对象，但要求 Namespace 已真实存在，
# 所以先幂等创建并打标签，再做完整文件的 server dry-run。
sudo "$KUBECTL" create namespace linux-lab \
  --dry-run=client \
  --output=yaml |
  sudo "$KUBECTL" apply --filename -
sudo "$KUBECTL" label namespace linux-lab \
  app.kubernetes.io/part-of=linux-lab \
  --overwrite

echo '== step 6: server dry-run =='
sudo "$KUBECTL" apply --dry-run=server --filename "$MANIFEST"

echo '== step 7: apply =='
sudo "$KUBECTL" apply --filename "$MANIFEST"
sudo "$KUBECTL" -n linux-lab rollout status \
  deployment/linux-lab-web \
  --timeout=180s
sudo "$KUBECTL" -n linux-lab get all -o wide

echo '== step 7: open the fixed NodePort =='
DEFAULT_IF="$(ip -4 route show default | awk 'NR == 1 {print $5}')"
FIREWALL_ZONE="$(sudo firewall-cmd --get-zone-of-interface="$DEFAULT_IF")"
test "$FIREWALL_ZONE" != 'no zone'
sudo firewall-cmd --permanent --zone="$FIREWALL_ZONE" --add-port=30080/tcp
sudo firewall-cmd --reload
sudo firewall-cmd --zone="$FIREWALL_ZONE" --query-port=30080/tcp

echo '== step 7: verify =='
VM_IP="$(
  ip -o -4 addr show dev "$DEFAULT_IF" scope global |
    awk 'NR == 1 {split($4, address, "/"); print address[1]}'
)"
curl --fail --show-error "http://${VM_IP}:30080/" | grep 'Linux Lab Web 0.1'

cat <<NOTE

Windows PowerShell 7 侧验证：
  \$VmIp = '$VM_IP'
  Test-NetConnection -ComputerName \$VmIp -Port 30080
  (Invoke-WebRequest -Uri "http://\${VmIp}:30080/" -UseBasicParsing).Content
NOTE
