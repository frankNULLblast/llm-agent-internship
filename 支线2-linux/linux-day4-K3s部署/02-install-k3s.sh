#!/usr/bin/env bash
# Day 4 步骤 2-4：firewalld 最小规则 → 下载并审阅安装脚本 → 固定版本安装 K3s
# 对应教材：Linux Day 4 → 分步操作 → 2./3./4.
#
# 红线：
#   - 不执行 curl ... | sh，先下载成文件、阅读、记录 SHA-256 再跑；
#   - 不关 SELinux、不停 firewalld、不用 --disable-selinux 绕过；
#   - 版本固定 v1.36.2+k3s1，不跟随 latest。
set -Eeuo pipefail

export LC_ALL=C

LAB_DIR="$HOME/linux-lab"
K3S_VERSION='v1.36.2+k3s1'
INSTALLER='/tmp/install-k3s.sh'

cd "$LAB_DIR"
mkdir -p evidence

echo '== step 2: keep firewalld, add the minimal K3s rules =='
# K3s 默认 Pod CIDR 10.42.0.0/16、Service CIDR 10.43.0.0/16，
# 按官方要求把这两个来源网段放进 trusted zone，让集群内部网络能通信。
# 单节点实验不需要其他机器加入，因此不对外开放 API 6443。
sudo firewall-cmd --permanent --zone=trusted --add-source=10.42.0.0/16
sudo firewall-cmd --permanent --zone=trusted --add-source=10.43.0.0/16
sudo firewall-cmd --reload
sudo firewall-cmd --zone=trusted --list-sources
sudo firewall-cmd --state

echo '== step 3: reachability of the installer and the SELinux RPM repo =='
getent hosts get.k3s.io
getent hosts rpm.rancher.io
curl --head --location --show-error --max-time 20 https://get.k3s.io/
curl --head --location --show-error --max-time 20 https://rpm.rancher.io/

echo '== step 3: download the installer as a plain file =='
curl --fail --location --show-error \
  https://get.k3s.io \
  --output "$INSTALLER"
chmod 0700 "$INSTALLER"
ls -l "$INSTALLER"
file "$INSTALLER"
sha256sum "$INSTALLER" | tee evidence/day04-k3s-installer.sha256

echo '== step 3: review the installer =='
# 人工阅读用 less；这里做机器可查的部分：关键变量与语法检查
grep -nE 'INSTALL_K3S_VERSION|INSTALL_K3S_EXEC|download|systemd|selinux' \
  "$INSTALLER" | head -n 80
bash -n "$INSTALLER"
cat <<'NOTE'
请先人工通读安装脚本的开头、版本变量、下载与 systemd 部分：
  less /tmp/install-k3s.sh
若在线脚本的 SHA-256 与之前记录的不同，必须重新阅读差异，不能机械接受。
NOTE

echo '== step 4: re-check the cgroup gate right before installing =='
CGROUP_FS="$(stat -fc %T /sys/fs/cgroup)"
PODMAN_CGROUP="$(podman info --format '{{.Host.CgroupsVersion}}' 2>/dev/null)"

if [[ "$CGROUP_FS" != cgroup2fs ||
      ! -r /sys/fs/cgroup/cgroup.controllers ||
      "$PODMAN_CGROUP" != v2 ]]; then
  printf 'STOP: K3s cgroup gate failed: fs=%s podman=%s\n' \
    "$CGROUP_FS" "$PODMAN_CGROUP" >&2
  exit 1
fi

echo '== step 4: install the pinned version with SELinux support =='
sudo env \
  INSTALL_K3S_VERSION="$K3S_VERSION" \
  INSTALL_K3S_EXEC='server --selinux' \
  sh "$INSTALLER"

echo '== verify binaries, service and SELinux policy package =='
test -x /usr/local/bin/k3s
test -x /usr/local/bin/kubectl
ls -l /usr/local/bin/k3s /usr/local/bin/kubectl
sudo systemctl status k3s --no-pager
sudo systemctl is-enabled k3s
sudo systemctl is-active k3s
sudo /usr/local/bin/k3s --version
sudo /usr/local/bin/kubectl version
rpm -q k3s-selinux
getenforce

echo '== wait for the node and system pods =='
sudo /usr/local/bin/kubectl get nodes -o wide
sudo /usr/local/bin/kubectl get pods -A
sudo /usr/local/bin/kubectl wait \
  --for=condition=Ready \
  node/linux-lab \
  --timeout=180s
sudo /usr/local/bin/kubectl get events -A \
  --sort-by=.metadata.creationTimestamp | tail -n 30

# kubeconfig 权限边界：管理员配置在 /etc/rancher/k3s/k3s.yaml，
# 一律用 sudo /usr/local/bin/kubectl 访问；
# 不复制到家目录、不 chmod 644、不提交到 Git。
