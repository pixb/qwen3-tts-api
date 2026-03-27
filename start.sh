#!/bin/bash
# Qwen3-TTS API 启动脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"
FILE_NAME="$(basename "${BASH_SOURCE[0]}" .sh)"

cd "${SCRIPT_DIR}" || exit

# 使用 uv 运行
uv run uvicorn api:app --host 0.0.0.0 --port 8001 --reload
