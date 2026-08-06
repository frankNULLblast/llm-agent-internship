#!/usr/bin/env bash
# 批量评测脚本（本机运行）
# 用法:  bash run_eval.sh             # 默认跑 test_questions.json
#        bash run_eval.sh 文件名.json  # 指定题集
set -euo pipefail
cd "$(dirname "$0")"
PY="/c/Users/rog 16/.workbuddy/binaries/python/envs/default/Scripts/python.exe"

set -a
[ -f .env ] && . ./.env
set +a
export DEEPSEEK_MODEL="${DEEPSEEK_MODEL:-deepseek-v4-flash}"

"$PY" eval.py "${1:-test_questions.json}"
