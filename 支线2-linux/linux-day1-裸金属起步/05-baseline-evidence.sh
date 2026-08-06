#!/usr/bin/env bash
# Day 1 步骤 10：创建学习仓库并生成第一份基线证据 evidence/day01-system.txt
# 对应教材：Linux Day 1 → 分步操作 → 10. 创建学习仓库和第一份证据
set -Eeuo pipefail

export LC_ALL=C

LAB_DIR="$HOME/linux-lab"

mkdir -p "$LAB_DIR/evidence"
cd "$LAB_DIR"

if [[ ! -d .git ]]; then
  git init
  git config user.name 'Linux Intern'
  git config user.email 'intern@example.invalid'
fi

if [[ ! -e .gitignore ]]; then
  cat > .gitignore <<'EOF'
.env
.venv/
.cache/
__pycache__/
.pytest_cache/
.mypy_cache/
*.py[cod]
*.oci
*.tar
*.tar.gz
*.tgz
downloads/
EOF
fi

# 采集基线证据。所有值均由命令实时产生，不预置任何输出。
{
  printf 'captured_at=%s\n' "$(date --iso-8601=seconds)"
  printf 'user=%s\n' "$(whoami)"
  printf 'hostname=%s\n' "$(hostname)"
  printf 'kernel=%s\n' "$(uname -r)"
  grep -E '^(NAME|VERSION|VERSION_ID)=' /etc/os-release
  printf 'selinux=%s\n' "$(getenforce)"
  printf 'sshd=%s\n' "$(systemctl is-active sshd)"
  printf 'firewalld=%s\n' "$(systemctl is-active firewalld)"
  ip -br address
  ip route
  df -hT /
} | tee evidence/day01-system.txt

echo '== secret scan =='
# 提交前自查：不得把密码、私钥、Token 写进仓库
git status --short
git diff --check
grep -RInE 'password|passwd|secret|token|BEGIN .*PRIVATE KEY' . \
  --exclude='.gitignore' || true

cat <<'NOTE'

确认扫描结果干净后再提交：
  git add .gitignore evidence/day01-system.txt
  git commit -m "docs: record Anolis lab baseline"
  git log --oneline -1

提交后关机并创建快照 day1-clean-install：
  sudo poweroff
NOTE
