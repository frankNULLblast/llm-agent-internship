#!/usr/bin/env bash
# ============================================================
# Day 2 全自动实践脚本 — 复制到 VM 的 ~/linux-lab/ 后运行
# 用法：bash day2-all.sh
# ============================================================
set -Eeuo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; NC='\033[0m'
say()  { echo -e "${CYAN}>>> $*${NC}"; }
pass() { echo -e "${GREEN}[OK] $*${NC}"; }
die()  { echo -e "${RED}[STOP] $*${NC}"; exit 1; }

say "=== 第 1 步：前置检查 ==="
cd ~/linux-lab
git status --short
lsblk -p -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT,MODEL
getenforce
pass "前置检查完成"

say "=== 第 2 步：文件/文本命令 ==="
mkdir -p evidence/day02-work/{docs/raw,archive}
cd evidence/day02-work
printf 'first line\nsecond line\n' > docs/raw/alpha.txt
cp docs/raw/alpha.txt docs/alpha-copy.txt
cat > animals.csv <<'CSVEOF'
id,name,type
1,panda,mammal
2,eagle,bird
3,tiger,mammal
4,crane,bird
5,yak,mammal
CSVEOF
head -n 3 animals.csv
wc -l -w -c animals.csv
grep -n 'mammal' animals.csv
grep -v '^id,' animals.csv | cut -d, -f3 | sort | uniq -c
tar -czf archive/day02-texts.tar.gz animals.csv docs
cd ~/linux-lab
pass "文件/文本命令完成"

say "======================================================"
say "  第 3 步：请手动在 VMware 里添加 5GB 练习盘"
say "  VMware → VM → Settings → Add → Hard Disk → SCSI"
say "  → 新建虚拟磁盘 → 5 GB → 确定"
say "  然后回到这里：sudo poweroff 关机，加盘后重新开机"
say "======================================================"
echo ""
read -r -p "盘加好了吗？按 Enter 继续，或按 Ctrl+C 退出..." _

say "=== 第 4 步：只读识别练习盘 ==="
echo ""
echo "下面三行是用来识别磁盘的。先看清楚输出："
echo ""
lsblk -p -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT,MODEL,SERIAL
echo ""
sudo fdisk -l /dev/sdb 2>/dev/null || echo "fdisk 暂时读不到 /dev/sdb"
sudo wipefs -n /dev/sdb 2>/dev/null || echo "wipefs 暂时读不到 /dev/sdb"
sudo blkid /dev/sdb 2>/dev/null || true

echo ""
echo "检查：/dev/sdb 大约 5GB、type=disk、无挂载点、无文件系统签名吗？"
read -r -p "确认无误则按 Enter 继续..." _

say "=== 第 5 步：安全门禁 ==="
unset SAFE_DATA_DISK
DATA_DISK=/dev/sdb
if [[ ! -b "$DATA_DISK" ]]; then
  die "不是块设备"
fi
T="$(lsblk -dn -o TYPE "$DATA_DISK")"
B="$(lsblk -dn -b -o SIZE "$DATA_DISK")"
R="$(lsblk -nr -o NAME "$DATA_DISK" | wc -l)"
M="$(lsblk -nr -o MOUNTPOINT "$DATA_DISK")"
S="$(sudo wipefs -n "$DATA_DISK" 2>&1)"
W=$?
if [[ "$T" != disk ]]; then die "不是整盘"; fi
if [[ ! "$B" =~ ^[0-9]+$ ]] || (( B < 5000000000 || B > 6000000000 )); then die "容量不在 5-6GB"; fi
if [[ "$R" -ne 1 ]]; then die "已有分区"; fi
if [[ -n "${M//[[:space:]]/}" ]]; then die "已挂载"; fi
if [[ "$W" -ne 0 ]]; then die "wipefs 失败"; fi
if [[ -n "${S//[[:space:]]/}" ]]; then die "已有文件系统签名"; fi

SAFE_DATA_DISK="$DATA_DISK"
pass "SAFE CHECK PASSED: $SAFE_DATA_DISK"

say "=== 第 6 步：GPT + XFS + UUID 开机挂载 ==="
echo ""
echo "这一步会格式化 /dev/sdb。确认继续吗？"
read -r -p '输入 FORMAT /dev/sdb 继续，其他任意键退出：' C
if [[ "$C" != 'FORMAT /dev/sdb' ]]; then
  die "用户取消格式化"
fi

sudo parted -s /dev/sdb mklabel gpt
sudo parted -s /dev/sdb mkpart primary xfs 1MiB 100%
sudo partprobe /dev/sdb && sudo udevadm settle
sudo mkfs.xfs -L linux_lab_data /dev/sdb1
sudo mkdir -p /srv/linux-lab-data && sudo mount /dev/sdb1 /srv/linux-lab-data
sudo blkid /dev/sdb1
findmnt /srv/linux-lab-data
df -hT /srv/linux-lab-data
pass "格式化并挂载完成"

say "=== fstab 写入 ==="
sudo test -e /etc/fstab.before-linux-lab || sudo cp -a /etc/fstab /etc/fstab.before-linux-lab
UUID="$(sudo blkid -s UUID -o value /dev/sdb1)"
if grep -qF "UUID=$UUID" /etc/fstab; then
  pass "fstab 已有此条目，跳过写入"
else
  printf 'UUID=%s /srv/linux-lab-data xfs defaults,nofail 0 0\n' "$UUID" | sudo tee -a /etc/fstab
fi
sudo findmnt --verify --verbose
sudo systemctl daemon-reload
sudo umount /srv/linux-lab-data && sudo mount -a
findmnt /srv/linux-lab-data
pass "fstab 写入完成，即将重启"

echo ""
echo "即将重启 VM。重启后请重新 SSH 进来，继续运行本脚本："
echo "  ssh intern@<IP>"
echo "  cd ~/linux-lab && bash day2-all.sh --resume"
echo ""
read -r -p "按 Enter 重启..." _
sudo reboot
