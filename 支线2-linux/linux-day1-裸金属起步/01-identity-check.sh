#!/usr/bin/env bash
# Day 1 步骤 4：第一次登录后的身份与系统标识检查（只读，不修改系统）
# 对应教材：Linux Day 1 → 分步操作 → 4. 第一次登录和身份检查
set -Eeuo pipefail

export LC_ALL=C

echo '== identity =='
whoami
id

echo '== sudo membership =='
# sudo -v 只刷新凭据缓存，不执行任何特权变更；intern 应属于 wheel 组
if id -nG | tr ' ' '\n' | grep -qx wheel; then
  echo 'WHEEL_MEMBER=yes'
else
  echo 'WHEEL_MEMBER=no'
fi

echo '== host and os =='
hostnamectl
grep -E '^(NAME|VERSION|VERSION_ID)=' /etc/os-release
if [[ -r /etc/anolis-release ]]; then
  cat /etc/anolis-release
else
  echo 'WARNING: /etc/anolis-release not found' >&2
fi
uname -r

echo '== time =='
timedatectl

# 教材要求的语义检查点：
#   whoami = intern
#   id 的组列表包含 wheel
#   Static hostname = linux-lab
#   VERSION_ID = 8.10
#   内核为龙蜥 an8 内核
#   时区 = Asia/Shanghai
#
# 主机名不正确时的修正命令（需要 sudo，本脚本不自动执行）：
#   sudo hostnamectl set-hostname linux-lab
