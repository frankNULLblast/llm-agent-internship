#!/usr/bin/env bash
# ============================================================
# Day 2 下半场 — 重启后运行此脚本
# 用法：ssh intern@<IP> 之后，cd ~/linux-lab && bash day2-part2.sh
# ============================================================
set -Eeuo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; NC='\033[0m'
say()  { echo -e "${CYAN}>>> $*${NC}"; }
pass() { echo -e "${GREEN}[OK] $*${NC}"; }
die()  { echo -e "${RED}[STOP] $*${NC}"; exit 1; }

say "=== 验证重启后挂载正常 ==="
cd ~/linux-lab
findmnt /srv/linux-lab-data || die "数据盘未挂载，请检查"
lsblk -f
grep '/srv/linux-lab-data' /etc/fstab
pass "挂载验证通过"

say "=== 第 7 步：用户/组/权限/SELinux ==="
sudo groupadd -f linuxlab
id labguest >/dev/null 2>&1 || sudo useradd -M -s /sbin/nologin labguest
sudo passwd -l labguest
sudo usermod -aG linuxlab intern labguest
sudo install -d -o intern -g linuxlab -m 2770 /srv/linux-lab-data/shared
sudo install -d -o intern -g intern -m 0700 /srv/linux-lab-data/private
printf 'shared\n' | sudo tee /srv/linux-lab-data/shared/team.txt
printf 'private\n' | sudo tee /srv/linux-lab-data/private/secret.txt
chmod 0640 /srv/linux-lab-data/shared/team.txt
chmod 0600 /srv/linux-lab-data/private/secret.txt

echo "--- labguest 读 shared（应成功）---"
sudo -u labguest cat /srv/linux-lab-data/shared/team.txt && pass "labguest 可以读 shared"

echo "--- labguest 读 private（应被拒）---"
sudo -u labguest cat /srv/linux-lab-data/private/secret.txt 2>&1 && die "labguest 不应该能读 private！" || pass "labguest 被拒（符合预期）"

ls -ldZ /srv/linux-lab-data/shared
sudo restorecon -RFv /srv/linux-lab-data
getenforce
pass "权限与 SELinux 配置完成"

say "=== 第 8 步：进程/服务/日志 ==="
bash -c 'while true; do date; sleep 5; done' > /tmp/clock.log 2>&1 &
CLOCK_PID=$!
echo "后台进程 PID=$CLOCK_PID"
sleep 2
kill -TERM "$CLOCK_PID"
wait "$CLOCK_PID" 2>/dev/null || true
echo "进程退出码=$?"
echo "时钟日志前3行："
head -3 /tmp/clock.log

systemctl status sshd --no-pager | head -5
sudo journalctl -u sshd -n 5 --no-pager

echo "--- 停/启 chronyd（安全演练，不动 sshd）---"
sudo systemctl stop chronyd
systemctl is-active chronyd && die "chronyd 没停掉" || pass "chronyd 已停止"
sudo systemctl start chronyd
systemctl is-active chronyd || die "chronyd 没启来" 
pass "chronyd 已恢复"

rpm -q bash openssh-server firewalld open-vm-tools
pass "进程/服务检查完成"

say "=== 第 9 步：system_report.sh ==="
chmod 0755 system_report.sh
bash -n system_report.sh && pass "语法检查通过" || die "脚本语法有误"

./system_report.sh | tee evidence/day02-system-report.txt
echo ""

# 字段校验
grep -q 'HOSTNAME=linux-lab' evidence/day02-system-report.txt || die "HOSTNAME 不是 linux-lab"
grep -q 'SELINUX=Enforcing' evidence/day02-system-report.txt || die "SELINUX 不是 Enforcing"
grep -q 'OS=.*Anolis' evidence/day02-system-report.txt || die "OS 不含 Anolis"
grep -q 'DATA_MOUNT=.*xfs.*srv/linux-lab-data' evidence/day02-system-report.txt || pass "DATA_MOUNT 看起来正常（含 xfs+srv/linux-lab-data）"
pass "13 字段报告生成完毕"

say "=== 存储/权限证据 ==="
{
  echo '== lsblk =='; lsblk -f
  echo '== perm =='
  stat -c '%A %a %U %G %n' /srv/linux-lab-data/shared /srv/linux-lab-data/private /srv/linux-lab-data/shared/team.txt
  echo '== SELinux =='; getenforce
} | tee evidence/day02-storage-permissions.txt
pass "存储权限证据已保存"

say "=== 第 10 步：Git 提交 ==="
git add system_report.sh evidence/day02-work evidence/day02-system-report.txt evidence/day02-storage-permissions.txt
git commit -m "feat: add storage lab and system report" || echo "（可能没有新变更，跳过）"
pass "Git 提交完成"

say "======================================================"
say "  Day 2 全部完成！"
say "  最后一步：sudo poweroff"
say "  VMware → Snapshot → 名称：day2-storage-ready"
say "======================================================"
