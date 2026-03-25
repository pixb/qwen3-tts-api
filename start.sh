#!/bin/bash
# Qwen3-TTS API 启动脚本

cd /home/pix/dev/code/ai/qwen3-tts

# 使用 uv 运行
uv run uvicorn api:app --host 0.0.0.0 --port 8001 --reload
