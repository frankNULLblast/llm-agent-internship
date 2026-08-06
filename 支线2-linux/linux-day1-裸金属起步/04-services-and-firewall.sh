#!/usr/bin/env bash
# Day 1 步骤 7：启动和检查基础服务，确认 SSH 已被 firewalld 放行
# 对应教材：Linux Day 1 → 分步操作 → 7. 启动和检查基础服务
#
# 红线：不关闭 SELinux，不长期关闭 firewalld，不启用 root SSH 登录。
set -Eeuo pipefail

export LC_ALL=C

echo '== enable and start =='
sudo systemctl enable --now sshd
sudo systemctl enable --now firewalld
sudo systemctl enable --now vmtoolsd

echo '== service state =='
for unit in sshd firewalld vmtoolsd; do
  printf '%s enabled=%s active=%s\n' \
    "$unit" \
    "$(systemctl is-enabled "$unit" 2>/dev/null || true)" \
    "$(systemctl is-active "$unit" 2>/dev/null || true)"
done

echo '== selinux =='
getenforce

echo '== firewall zone of the default interface =='
VM_IF="$(ip -4 route show default | awk 'NR == 1 {print $5}')"
FIREWALL_ZONE="$(sudo firewall-cmd --get-zone-of-interface="$VM_IF")"
test -n "$FIREWALL_ZONE"
test "$FIREWALL_ZONE" != 'no zone'
printf 'VM_IF=%s FIREWALL_ZONE=%s\n' "$VM_IF" "$FIREWALL_ZONE"

echo '== sshd listener =='
sudo ss -lntp | grep ':22 '

echo '== active zones and services =='
sudo firewall-cmd --get-active-zones
sudo firewall-cmd --zone="$FIREWALL_ZONE" --list-services

# 只在缺少 ssh 服务时补这一项，不批量开放端口
if sudo firewall-cmd --zone="$FIREWALL_ZONE" --query-service=ssh >/dev/null; then
  echo 'SSH_SERVICE_ALREADY_ALLOWED=yes'
else
  echo 'adding the ssh service to the active zone'
  sudo firewall-cmd --permanent --zone="$FIREWALL_ZONE" --add-service=ssh
  sudo firewall-cmd --reload
  sudo firewall-cmd --zone="$FIREWALL_ZONE" --list-services
fi

# 预期：sshd / firewalld / vmtoolsd 均为 enabled + active，SELinux 为 Enforcing
