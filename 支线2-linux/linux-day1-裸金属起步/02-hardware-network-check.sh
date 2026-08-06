#!/usr/bin/env bash
# Day 1 步骤 5：检查硬件、磁盘与网络（只读）
# 对应教材：Linux Day 1 → 分步操作 → 5. 检查硬件、磁盘与网络
set -Eeuo pipefail

export LC_ALL=C

echo '== memory =='
free -h

echo '== block devices =='
# Day 1 只应有一块约 80GB 的系统盘；5GB 练习盘留到 Day 2 再添加
lsblk -p -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT,MODEL

echo '== filesystems =='
df -hT

echo '== address and route =='
ip -br address
ip route

echo '== resolver =='
cat /etc/resolv.conf

echo '== derived values =='
VM_IF="$(ip -4 route show default | awk 'NR == 1 {print $5}')"
if [[ -z "$VM_IF" ]]; then
  echo 'STOP: no default route; check the VMware NAT adapter' >&2
  exit 1
fi
VM_IP="$(
  ip -o -4 addr show dev "$VM_IF" scope global |
    awk 'NR == 1 {split($4, address, "/"); print address[1]}'
)"
printf '默认网卡：%s\n虚拟机IP：%s\n' "$VM_IF" "$VM_IP"

echo '== connectivity =='
# 回环 → 本机地址 → DNS 解析 → HTTPS，逐层验证，不跳步
ping -c 3 127.0.0.1
ping -c 3 "$VM_IP"
getent hosts mirrors.openanolis.cn
curl -I --max-time 15 https://mirrors.openanolis.cn/
