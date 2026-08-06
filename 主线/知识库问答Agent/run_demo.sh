#!/usr/bin/env bash
# 知识库问答 Agent —— 本机演示脚本（不依赖任何沙箱）
# 用法:  bash run_demo.sh "你的问题"
set -euo pipefail
cd "$(dirname "$0")"
PY="/c/Users/rog 16/.workbuddy/binaries/python/envs/default/Scripts/python.exe"

# 加载本目录的 .env（含 DEEPSEEK_API_KEY 与 DEEPSEEK_MODEL）
set -a
[ -f .env ] && . ./.env
set +a

# 强制使用可用模型（覆盖 .env 中可能过时的 deepseek-v1-tflash）
export DEEPSEEK_MODEL="${DEEPSEEK_MODEL:-deepseek-v4-flash}"

if [ -z "${DEEPSEEK_API_KEY:-}" ]; then
  echo "错误：未检测到 DEEPSEEK_API_KEY，请在本目录 .env 中填写你的 DeepSeek key" >&2
  exit 1
fi

"$PY" agent.py "$1"
