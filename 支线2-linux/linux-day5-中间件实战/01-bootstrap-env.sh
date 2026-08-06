#!/usr/bin/env bash
# Day 5 步骤 1-2：准备 middleware 目录，只在首次运行时生成本地 .env
# 对应教材：Linux Day 5 → 分步操作 → 1. 创建配置目录和 .env.example / 2. 只在首次运行时生成本地 .env
#
# 红线：密码随机生成到权限 600 的 .env，不进 Git、不进截图、不进 evidence。
set -Eeuo pipefail

export LC_ALL=C

LAB_DIR="$HOME/linux-lab"
cd "$LAB_DIR"
mkdir -p middleware

echo '== gitignore coverage =='
# 秘密、虚拟环境、缓存和 OCI 包都必须已被忽略
grep -nE '^(\.env|\.venv/|\.cache/|__pycache__/|\.pytest_cache/|\.mypy_cache/|\*\.py\[cod\]|\*\.oci|\*\.tar|\*\.tar\.gz|\*\.tgz)$' \
  .gitignore

echo '== local .env =='
if [[ -e middleware/.env ]]; then
  echo 'middleware/.env already exists; refusing to overwrite it'
else
  (
    umask 077
    MYSQL_PASSWORD_VALUE="$(openssl rand -hex 24)"
    MYSQL_ROOT_PASSWORD_VALUE="$(openssl rand -hex 24)"
    RABBITMQ_PASSWORD_VALUE="$(openssl rand -hex 24)"

    cat > middleware/.env <<EOF
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_DATABASE=linux_lab
MYSQL_USER=labapp
MYSQL_PASSWORD=${MYSQL_PASSWORD_VALUE}
MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD_VALUE}
RABBITMQ_HOST=127.0.0.1
RABBITMQ_PORT=5672
RABBITMQ_DEFAULT_USER=labmq
RABBITMQ_DEFAULT_PASS=${RABBITMQ_PASSWORD_VALUE}
EOF

    chmod 0600 middleware/.env
  )
  echo 'middleware/.env created'
fi

echo '== metadata only, never the contents =='
stat -c '%A %a %U %G %n' middleware/.env
git check-ignore -v middleware/.env
git status --short

echo '== init.sql permissions =='
# 显式 0644：避免严格 umask 让容器内的 MySQL 用户读不到这个文件
chmod 0644 middleware/init.sql
stat -c '%A %a %U %G %n' middleware/init.sql

echo '== python virtual environment =='
if [[ ! -d .venv ]]; then
  python3.11 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install --requirement middleware/requirements.txt
python -m pip check
# 版本必须精确为 1.4.2 和 9.7.0
python -c 'import pika, mysql.connector; print(pika.__version__, mysql.connector.__version__)'
python -m py_compile middleware/send_event.py middleware/consume_once.py

cat <<'NOTE'

每次打开新终端，都要这样加载环境（不要 cat .env，不要把 env 输出存成证据）：
  cd "$HOME/linux-lab"
  source .venv/bin/activate
  set -a
  source middleware/.env
  set +a

实验结束可从当前 shell 清除秘密变量：
  unset MYSQL_PASSWORD MYSQL_ROOT_PASSWORD RABBITMQ_DEFAULT_PASS
NOTE
