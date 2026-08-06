#!/usr/bin/env bash
# Day 3 步骤 1-3：按「地址 → 路由 → DNS → 端口/防火墙 → 应用」五层顺序排错（只读）
# 对应教材：Linux Day 3 → 分步操作 → 1./2./3.
set -Eeuo pipefail

export LC_ALL=C

echo '== derived values =='
DEFAULT_IF="$(ip -4 route show default | awk 'NR == 1 {print $5}')"
VM_IP="$(
  ip -o -4 addr show dev "$DEFAULT_IF" scope global |
    awk 'NR == 1 {split($4, address, "/"); print address[1]}'
)"
FIREWALL_ZONE="$(sudo firewall-cmd --get-zone-of-interface="$DEFAULT_IF")"
printf 'DEFAULT_IF=%s\nVM_IP=%s\nFIREWALL_ZONE=%s\n' \
  "$DEFAULT_IF" "$VM_IP" "$FIREWALL_ZONE"
test -n "$DEFAULT_IF"
test -n "$VM_IP"
test -n "$FIREWALL_ZONE"
test "$FIREWALL_ZONE" != 'no zone'

echo '== layer 1: address =='
ip -br link
ip -br addr

echo '== layer 2: route =='
ip route
ip route get 1.1.1.1
nmcli device status
nmcli -f NAME,UUID,TYPE,DEVICE connection show --active
nmcli device show "$DEFAULT_IF" | grep -E 'IP4\.(ADDRESS|GATEWAY|DNS)'

echo '== layer 3: dns =='
# getent 走系统统一名称服务；dig 专门观察 DNS，两者视角不同
getent hosts mirrors.openanolis.cn
dig mirrors.openanolis.cn A +short
ping -c 4 "$(ip route | awk '/^default/ {print $3; exit}')"
ping -c 4 mirrors.openanolis.cn
curl -I --max-time 10 https://mirrors.openanolis.cn/
traceroute -n -m 8 1.1.1.1 || true

echo '== dns failure drill =='
# 192.0.2.0/24 是 RFC 5737 文档示例网段，这次查询应当超时。
# 只用参数指定一台不存在的 DNS，不去改 /etc/resolv.conf。
dig @192.0.2.1 example.com A +time=1 +tries=1 || true
printf 'exit_code=%s\n' "$?"
echo '-- system resolver should still work --'
dig example.com A +short

echo '== layer 4: ports and firewall =='
ss -lntup
sudo lsof -nP -iTCP:22 -sTCP:LISTEN
sudo firewall-cmd --state
sudo firewall-cmd --get-active-zones
sudo firewall-cmd --zone="$FIREWALL_ZONE" --list-all
sudo firewall-cmd --zone="$FIREWALL_ZONE" --query-service=ssh
