#!/usr/bin/env bash
# Day 1 步骤 6：更新系统并安装基础工具（需要 sudo，会修改系统）
# 对应教材：Linux Day 1 → 分步操作 → 6. 更新系统并安装基础工具
#
# 注意：本脚本会执行 dnf upgrade，可能安装新内核。
# 完成后需要手动 sudo reboot 才会使用新内核，本脚本不自动重启。
set -Eeuo pipefail

export LC_ALL=C

echo '== repositories =='
dnf repolist

echo '== metadata =='
sudo dnf makecache

echo '== upgrade =='
sudo dnf upgrade -y

echo '== base tools =='
# 教材固定清单：全部来自龙蜥官方仓库，不添加第三方源
sudo dnf install -y \
  bash-completion \
  bind-utils \
  chrony \
  curl \
  firewalld \
  git \
  jq \
  lsof \
  nano \
  open-vm-tools \
  openssh-server \
  parted \
  policycoreutils-python-utils \
  python3 \
  tar \
  traceroute \
  tree \
  unzip \
  vim-enhanced \
  wget \
  xfsprogs

echo '== rpm dependency check =='
sudo dnf check

echo '== kernel comparison =='
# 运行中内核与已安装内核包对照；两者不一致说明需要重启
uname -r
rpm -q kernel

cat <<'NOTE'

下一步（手动执行）：
  sudo reboot
重启后用 intern 重新登录，再运行 04-services-and-firewall.sh。
NOTE
