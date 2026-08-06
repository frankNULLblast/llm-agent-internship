#!/usr/bin/env bash
# Day 3 步骤 4：临时 Web 服务 + 只用运行时防火墙规则的完整开关演练
# 对应教材：Linux Day 3 → 分步操作 → 4. 启动临时 Web 服务并只开放运行时端口
#
# 用法：
#   ./02-temp-http-drill.sh open    # 准备页面 + 加运行时规则，然后手动起服务
#   ./02-temp-http-drill.sh verify  # 在另一个终端验证监听与访问
#   ./02-temp-http-drill.sh close   # Ctrl+C 停服务后撤销规则并证明端口已关闭
#
# 关键点：全程不使用 --permanent，8000 不会留在持久配置里。
set -Eeuo pipefail

export LC_ALL=C

LAB_DIR="$HOME/linux-lab"
HTTP_DIR="$LAB_DIR/evidence/day03-http"
PORT=8000

resolve_network() {
  DEFAULT_IF="$(ip -4 route show default | awk 'NR == 1 {print $5}')"
  VM_IP="$(
    ip -o -4 addr show dev "$DEFAULT_IF" scope global |
      awk 'NR == 1 {split($4, address, "/"); print address[1]}'
  )"
  FIREWALL_ZONE="$(sudo firewall-cmd --get-zone-of-interface="$DEFAULT_IF")"
  test "$FIREWALL_ZONE" != 'no zone'
}

action="${1:-}"

case "$action" in
  open)
    mkdir -p "$HTTP_DIR"
    cat > "$HTTP_DIR/index.html" <<'EOF'
<!doctype html>
<html lang="zh-CN">
  <head><meta charset="utf-8"><title>Linux Day 3</title></head>
  <body><h1>temporary web works</h1></body>
</html>
EOF
    resolve_network
    # 运行时规则：立即生效，重启后自动消失
    sudo firewall-cmd --zone="$FIREWALL_ZONE" --add-port="${PORT}/tcp"
    sudo firewall-cmd --zone="$FIREWALL_ZONE" --query-port="${PORT}/tcp"
    cat <<NOTE

现在在本终端（终端 A）前台启动服务：
  cd "$HTTP_DIR"
  python3 -m http.server $PORT --bind "$VM_IP"

看到 "Serving HTTP on ... port $PORT" 后保持终端 A 打开，
到终端 B 运行：./02-temp-http-drill.sh verify
NOTE
    ;;

  verify)
    resolve_network
    curl --fail --show-error "http://${VM_IP}:${PORT}/"
    ss -lntp "( sport = :${PORT} )"
    sudo lsof -nP -iTCP:"$PORT" -sTCP:LISTEN
    cat <<NOTE

Windows PowerShell 7 侧验证（预期 200，正文含 temporary web works）：
  \$VmIp = '$VM_IP'
  Test-NetConnection -ComputerName \$VmIp -Port $PORT
  Invoke-WebRequest -Uri "http://\${VmIp}:${PORT}/" -UseBasicParsing |
    Select-Object StatusCode, Content
NOTE
    ;;

  close)
    resolve_network
    sudo firewall-cmd --zone="$FIREWALL_ZONE" --remove-port="${PORT}/tcp"
    # 预期输出 no：从未写过 --permanent，系统配置里也不会残留 8000
    sudo firewall-cmd --zone="$FIREWALL_ZONE" --query-port="${PORT}/tcp" || true
    ss -lntp "( sport = :${PORT} )" || true
    curl --max-time 2 "http://${VM_IP}:${PORT}/" ||
      echo 'expected: service is stopped'
    ;;

  *)
    echo "usage: $0 {open|verify|close}" >&2
    exit 2
    ;;
esac
