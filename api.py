"""
Qwen3-TTS FastAPI Server (Legacy Entry Point)
基于 Qwen3-TTS 实现文字转语音、语音克隆、语音设计功能

注意：此文件已废弃，请使用 src/qwen3_tts_api/main.py 或 
通过 `python -m qwen3_tts_api` 运行
"""

# 导入新模块
from src.qwen3_tts_api.main import app


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
