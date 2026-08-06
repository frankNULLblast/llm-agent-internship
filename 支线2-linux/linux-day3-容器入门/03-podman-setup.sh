#!/usr/bin/env bash
# Day 3 步骤 5：安装并确认 rootless Podman
# 对应教材：Linux Day 3 → 分步操作 → 5. 安装并确认 rootless Podman
#
# 红线：主线容器命令一律以 intern 直接运行，不加 sudo。
set -Eeuo pipefail

export LC_ALL=C

echo '== install from the Anolis AppStream repository =='
# 不添加 Docker 的第三方仓库
sudo dnf install -y podman slirp4netns fuse-overlayfs

echo '== version and rootless mode =='
podman --version
podman info --format 'rootless={{.Host.Security.Rootless}}'
podman unshare cat /proc/self/uid_map

echo '== subordinate uid/gid =='
if grep -q "^${USER}:" /etc/subuid && grep -q "^${USER}:" /etc/subgid; then
  grep "^${USER}:" /etc/subuid /etc/subgid
  echo 'SUBID_PRESENT=yes'
else
  echo 'SUBID_PRESENT=no'
  cat <<'NOTE'
缺少 subordinate UID/GID 时，分配一段不与其他用户重叠的范围，然后重新登录：
  sudo usermod --add-subuids 100000-165535 intern
  sudo usermod --add-subgids 100000-165535 intern
若 intern 已有范围，不要重复修改。
NOTE
fi

echo '== linger for rootless background containers =='
# 不开 linger 的话，最后一个 SSH 会话退出后 rootless 后台容器可能一起停止
sudo loginctl enable-linger intern
loginctl show-user intern -p Linger

# 预期：rootless=true，且 Linger=yes（精确输出）
# 教程结束后如不再需要，可用 sudo loginctl disable-linger intern 回退
