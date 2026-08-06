#!/usr/bin/env bash
# Day 4 步骤 1：K3s 硬门禁检查 —— 内核 >= 5.8、cgroup v2、SELinux、firewalld
# 对应教材：Linux Day 4 → 分步操作 → 1. 检查内核、cgroup、SELinux 与防火墙
#
# 这一步是硬性前置条件，不是「看一眼就继续」。
# Kubernetes 1.36 的 kubelet 默认拒绝 cgroup v1。
#
# 用法：
#   ./01-preflight-cgroup.sh check    # 只读检查，打印门禁结论
#   ./01-preflight-cgroup.sh enable   # 仅在 CGROUP_FS=tmpfs 时给默认内核加启动参数并重启
#   ./01-preflight-cgroup.sh verify   # 重启后复核
#   ./01-preflight-cgroup.sh rollback # 移除该启动参数
#
# 前提：已在切换启动参数前创建快照 day4-pre-k3s-cgroup。
set -Eeuo pipefail

export LC_ALL=C

LAB_DIR="$HOME/linux-lab"

collect_gate_values() {
  KERNEL_RELEASE="$(uname -r)"
  KERNEL_BASE="${KERNEL_RELEASE%%-*}"
  CGROUP_FS="$(stat -fc %T /sys/fs/cgroup)"

  if [[ "$(printf '5.8\n%s\n' "$KERNEL_BASE" | sort -V | head -n 1)" == 5.8 ]]; then
    KERNEL_AT_LEAST_58=yes
  else
    KERNEL_AT_LEAST_58=no
  fi

  if grep -qw cgroup2 /proc/filesystems; then
    CGROUP2_SUPPORTED=yes
  else
    CGROUP2_SUPPORTED=no
  fi
}

action="${1:-check}"

case "$action" in
  check)
    echo '== virtualisation and cgroup mount =='
    uname -r
    systemd-detect-virt
    mount | grep ' /sys/fs/cgroup ' || true

    collect_gate_values
    printf 'KERNEL_RELEASE=%s\nKERNEL_AT_LEAST_58=%s\nCGROUP_FS=%s\nCGROUP2_SUPPORTED=%s\n' \
      "$KERNEL_RELEASE" "$KERNEL_AT_LEAST_58" "$CGROUP_FS" "$CGROUP2_SUPPORTED"
    grep -E '(^| )cgroup' /proc/filesystems

    echo '== security =='
    getenforce
    sestatus
    systemctl is-active firewalld

    echo '== firewalld zone =='
    DEFAULT_IF="$(ip -4 route show default | awk 'NR == 1 {print $5}')"
    FIREWALL_ZONE="$(sudo firewall-cmd --get-zone-of-interface="$DEFAULT_IF")"
    sudo firewall-cmd --get-active-zones
    sudo firewall-cmd --zone="$FIREWALL_ZONE" --list-all

    echo '== gate verdict =='
    if [[ "$KERNEL_AT_LEAST_58" != yes || "$CGROUP2_SUPPORTED" != yes ]]; then
      echo 'STOP: kernel or cgroup2 support does not meet the hard gate' >&2
      exit 1
    elif [[ "$CGROUP_FS" == cgroup2fs ]]; then
      echo 'CGROUP V2 ALREADY ACTIVE: no boot entry change is needed'
    elif [[ "$CGROUP_FS" == tmpfs ]]; then
      echo 'ACTION REQUIRED: run "./01-preflight-cgroup.sh enable" to switch to cgroup v2'
    else
      echo "STOP: unexpected cgroup filesystem: $CGROUP_FS" >&2
      exit 1
    fi
    ;;

  enable)
    collect_gate_values
    cd "$LAB_DIR"

    if [[ "$KERNEL_AT_LEAST_58" != yes || "$CGROUP2_SUPPORTED" != yes ]]; then
      echo 'STOP: kernel or cgroup2 support does not meet the hard gate' >&2
      exit 1
    elif [[ "$CGROUP_FS" == cgroup2fs ]]; then
      echo 'CGROUP V2 ALREADY ACTIVE: no boot entry was changed'
      exit 0
    elif [[ "$CGROUP_FS" != tmpfs ]]; then
      echo "STOP: unexpected cgroup filesystem: $CGROUP_FS" >&2
      exit 1
    fi

    rpm -q grubby || sudo dnf install -y grubby
    DEFAULT_KERNEL="$(sudo grubby --default-kernel)"
    CURRENT_KERNEL="/boot/vmlinuz-$(uname -r)"
    printf 'CURRENT_KERNEL=%s\nDEFAULT_KERNEL=%s\n' \
      "$CURRENT_KERNEL" "$DEFAULT_KERNEL"

    # 只改「当前正在用且同时是默认项」的内核，保留其他内核作为恢复入口
    if [[ "$DEFAULT_KERNEL" != "$CURRENT_KERNEL" ]]; then
      echo 'STOP: the running kernel is not the default boot kernel' >&2
      exit 1
    fi

    mkdir -p evidence
    printf '%s\n' "$DEFAULT_KERNEL" > evidence/day04-cgroup-kernel.txt

    if sudo grubby --update-kernel="$DEFAULT_KERNEL" \
         --args='systemd.unified_cgroup_hierarchy=1' &&
       sudo grubby --info="$DEFAULT_KERNEL" |
         grep 'systemd.unified_cgroup_hierarchy=1'; then
      echo 'Boot argument added to the default kernel; rebooting now'
      sudo reboot
    else
      echo 'STOP: boot entry update failed; do not reboot blindly' >&2
      exit 1
    fi
    ;;

  verify)
    cd "$LAB_DIR"
    cat /proc/cmdline
    CURRENT_KERNEL="/boot/vmlinuz-$(uname -r)"
    EXPECTED_KERNEL="$(
      if [[ -s evidence/day04-cgroup-kernel.txt ]]; then
        cat evidence/day04-cgroup-kernel.txt
      else
        printf '%s\n' "$CURRENT_KERNEL"
      fi
    )"
    CGROUP_FS="$(stat -fc %T /sys/fs/cgroup)"
    PODMAN_CGROUP="$(podman info --format '{{.Host.CgroupsVersion}}' 2>/dev/null)"

    if [[ "$CURRENT_KERNEL" != "$EXPECTED_KERNEL" ]]; then
      echo 'STOP: rebooted into a kernel other than the intended entry' >&2
      exit 1
    elif [[ "$CGROUP_FS" != cgroup2fs ]]; then
      echo "STOP: expected cgroup2fs, got $CGROUP_FS" >&2
      exit 1
    elif [[ ! -r /sys/fs/cgroup/cgroup.controllers ]]; then
      echo 'STOP: cgroup v2 controllers file is unreadable' >&2
      exit 1
    elif [[ "$PODMAN_CGROUP" != v2 ]]; then
      echo "STOP: Podman reports cgroup version $PODMAN_CGROUP" >&2
      exit 1
    else
      echo 'K3S CGROUP GATE PASSED'
      podman info \
        --format 'rootless={{.Host.Security.Rootless}} cgroupVersion={{.Host.CgroupsVersion}}'
    fi

    echo '== kernel modules and forwarding =='
    lsmod | grep -E 'overlay|br_netfilter' || true
    sudo modprobe overlay
    sudo modprobe br_netfilter
    sysctl net.ipv4.ip_forward
    sysctl net.bridge.bridge-nf-call-iptables

    echo '== SELinux container policy dependencies =='
    sudo dnf install -y \
      container-selinux \
      policycoreutils \
      policycoreutils-python-utils
    rpm -q container-selinux policycoreutils policycoreutils-python-utils
    ;;

  rollback)
    cd "$LAB_DIR"
    if [[ -s evidence/day04-cgroup-kernel.txt ]]; then
      TARGET_KERNEL="$(cat evidence/day04-cgroup-kernel.txt)"
    else
      TARGET_KERNEL="$(sudo grubby --default-kernel)"
    fi

    # 只删这一项参数，不覆盖其他内核参数
    if sudo grubby --update-kernel="$TARGET_KERNEL" \
         --remove-args='systemd.unified_cgroup_hierarchy=1'; then
      sudo grubby --info="$TARGET_KERNEL"
      sudo reboot
    else
      echo 'STOP: failed to remove the cgroup argument; restore the snapshot' >&2
      exit 1
    fi
    ;;

  *)
    echo "usage: $0 {check|enable|verify|rollback}" >&2
    exit 2
    ;;
esac
