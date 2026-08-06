#!/usr/bin/env bash
set -Eeuo pipefail

export LC_ALL=C

# --- os-release ---
if [[ -r /etc/os-release ]]; then
  # shellcheck disable=SC1091
  source /etc/os-release
else
  echo 'ERROR: /etc/os-release is not readable' >&2
  exit 1
fi

# --- network ---
default_route="$(ip -4 route show default | head -n 1 || true)"
default_interface="$(awk '{print $5}' <<<"$default_route")"

if [[ -n "$default_interface" ]]; then
  default_ipv4="$(
    ip -o -4 addr show dev "$default_interface" scope global |
      awk 'NR == 1 {split($4, address, "/"); print address[1]}'
  )"
else
  default_interface='NONE'
  default_ipv4='NONE'
fi

if [[ -z "$default_ipv4" ]]; then
  default_ipv4='NONE'
fi

# --- memory ---
memory_summary="$(
  free -h |
    awk '/^Mem:/ {printf "%s total, %s used, %s available", $2, $3, $7}'
)"

# --- root filesystem ---
root_summary="$(
  df -hT / |
    awk 'NR == 2 {printf "%s on %s, %s used, %s available", $2, $7, $6, $5}'
)"

# --- data mount ---
data_mount="$(
  findmnt -n -o SOURCE,FSTYPE,TARGET /srv/linux-lab-data 2>/dev/null ||
    printf 'NOT_MOUNTED'
)"

# --- services ---
service_state() {
  local unit="$1"
  systemctl is-active "$unit" 2>/dev/null || true
}

# --- report ---
printf 'REPORT_TIME=%s\n' "$(date --iso-8601=seconds)"
printf 'HOSTNAME=%s\n' "$(hostname)"
printf 'OS=%s %s\n' "${NAME:-unknown}" "${VERSION_ID:-unknown}"
printf 'KERNEL=%s\n' "$(uname -r)"
printf 'DEFAULT_INTERFACE=%s\n' "$default_interface"
printf 'DEFAULT_IPV4=%s\n' "$default_ipv4"
printf 'MEMORY=%s\n' "$memory_summary"
printf 'ROOT_FS=%s\n' "$root_summary"
printf 'DATA_MOUNT=%s\n' "$data_mount"
printf 'SERVICE_SSHD=%s\n' "$(service_state sshd)"
printf 'SERVICE_FIREWALLD=%s\n' "$(service_state firewalld)"
printf 'SERVICE_VMTOOLSD=%s\n' "$(service_state vmtoolsd)"
printf 'SELINUX=%s\n' "$(getenforce)"
