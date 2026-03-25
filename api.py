"""
Qwen3-TTS FastAPI Server
基于 Qwen3-TTS 实现文字转语音、语音克隆、语音设计功能
"""

import os
import re
import uuid
import shutil
import torch
import soundfile as sf
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

# ==================== 配置 ====================
MODEL_NAME = "Qwen/Qwen3-TTS-12Hz-0.6B-Base"
DEFAULT_LANGUAGE = "English"
DEFAULT_TEMPERATURE = 0.8
DEFAULT_EXAGGERATION = 0.5

# 支持的语言列表
SUPPORTED_LANGUAGES = [
    "Chinese",
    "English",
    "Japanese",
    "Korean",
    "German",
    "French",
    "Russian",
    "Portuguese",
    "Spanish",
    "Italian",
]

# 语言代码映射
LANGUAGE_CODE_MAP = {
    "zh": "Chinese",
    "cn": "Chinese",
    "chinese": "Chinese",
    "en": "English",
    "english": "English",
    "ja": "Japanese",
    "japanese": "Japanese",
    "ko": "Korean",
    "korean": "Korean",
    "de": "German",
    "german": "German",
    "fr": "French",
    "french": "French",
    "ru": "Russian",
    "russian": "Russian",
    "pt": "Portuguese",
    "portuguese": "Portuguese",
    "es": "Spanish",
    "spanish": "Spanish",
    "it": "Italian",
    "italian": "Italian",
}

# ==================== FastAPI 初始化 ====================
app = FastAPI(
    title="Qwen3-TTS API",
    version="1.0.0",
    description="Qwen3 Text-to-Speech API with voice cloning and voice design support",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 目录和设备 ====================
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("output")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

device = "cuda" if torch.cuda.is_available() else "cpu"
model = None


# ==================== 语言检测 ====================
def detect_language(text: str) -> str:
    """
    检测文本语言，返回 Qwen3-TTS 支持的语言名称
    """
    # 中文检测
    if re.search(r"[\u4e00-\u9fff]", text):
        return "Chinese"
    # 日语检测
    if re.search(r"[\u3040-\u309f\u30a0-\u30ff]", text):
        return "Japanese"
    # 韩语检测
    if re.search(r"[\uac00-\ud7af]", text):
        return "Korean"
    # 俄语检测
    if re.search(r"[\u0400-\u04ff]", text):
        return "Russian"
    # 德语检测 (德语特殊字符)
    if re.search(r"[äöüßÄÖÜ]", text):
        return "German"
    # 法语检测 (法语特殊字符)
    if re.search(r"[àâäéèêëïîôùûüÿç]", text, re.IGNORECASE):
        return "French"
    # 葡萄牙语检测
    if re.search(r"[ãõàáâéêíóôúüç]", text, re.IGNORECASE):
        return "Portuguese"
    # 西班牙语检测 (西班牙语特殊字符)
    if re.search(r"[áéíóúüñ¿¡]", text, re.IGNORECASE):
        return "Spanish"
    # 意大利语检测 (意大利语特殊字符)
    if re.search(r"[àèéìíîòóùú]", text, re.IGNORECASE):
        return "Italian"

    return "English"


def normalize_language(language: Optional[str]):
    """
    标准化语言参数
    """
    if not language or language.lower() == "auto":
        return None  # 返回 None 表示自动检测

    lang_lower = language.lower().strip()
    return LANGUAGE_CODE_MAP.get(lang_lower, language.capitalize())


# ==================== 模型加载 ====================
def get_model():
    """
    懒加载模型
    """
    global model
    if model is None:
        print(f"Loading Qwen3-TTS Model on {device}...")
        from qwen_tts import Qwen3TTSModel

        # 根据设备选择 dtype
        dtype = torch.bfloat16 if device == "cuda" else torch.float32

        model = Qwen3TTSModel.from_pretrained(
            MODEL_NAME,
            device_map=device,
            dtype=dtype,
        )
        print(f"Model loaded successfully on {device}")
    return model


# ==================== 工具函数 ====================
def cleanup_file(path: Path):
    """清理单个文件"""
    if path and path.exists():
        try:
            path.unlink()
            print(f"Cleaned up: {path}")
        except Exception as e:
            print(f"Cleanup error: {e}")


def save_upload_file(upload_file: UploadFile, destination: Path) -> Path:
    """保存上传的文件"""
    with open(destination, "wb") as f:
        shutil.copyfileobj(upload_file.file, f)
    return destination


def save_audio(wavs, sr, output_path: Path) -> Path:
    """保存音频文件"""
    # 处理批量结果
    if isinstance(wavs, (list, tuple)) and len(wavs) > 0:
        wav = wavs[0]
    else:
        wav = wavs

    # 转换为 numpy 并保存
    if isinstance(wav, torch.Tensor):
        wav = wav.cpu().numpy()

    sf.write(str(output_path), wav, sr)
    return output_path


def adjust_audio_speed(wav, sr, speed_rate: float) -> tuple:
    """
    调整音频速度
    speed_rate: 1.0 = 原始速度, >1.0 = 加速, <1.0 = 减速
    使用重采样方式，会同时改变音调但更稳定
    """
    import numpy as np
    import resampy

    if speed_rate == 1.0:
        return wav, sr

    if wav.dtype != np.float32:
        wav = wav.astype(np.float32)

    if wav.max() > 1.0:
        wav = wav / 32768.0

    new_sr = int(sr * speed_rate)
    wav_adjusted = resampy.resample(wav, sr_orig=sr, sr_new=new_sr)

    return wav_adjusted, new_sr


# ==================== API 路由 ====================
@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "device": device,
        "model": MODEL_NAME,
        "supported_languages": SUPPORTED_LANGUAGES,
    }


@app.get("/languages")
async def get_languages():
    """获取支持的语言列表"""
    return {"languages": SUPPORTED_LANGUAGES, "default": DEFAULT_LANGUAGE}


@app.post("/tts", response_class=FileResponse)
async def text_to_speech(
    text: str = Form(...),
    language: Optional[str] = Form("Auto"),
    exaggeration: float = Form(DEFAULT_EXAGGERATION),
    temperature: float = Form(DEFAULT_TEMPERATURE),
    instruct: Optional[str] = Form(None),
    audio_prompt: Optional[UploadFile] = File(None),
    speed_rate: float = Form(1.0),
):
    """
    文字转语音 (Voice Clone 方式)

    - **text**: 要转换的文本 (必填)
    - **language**: 语言 (默认自动检测)
    - **exaggeration**: 情感夸张程度 0.0-1.0 (默认 0.5)
    - **temperature**: 采样温度 0.0-1.0 (默认 0.8)
    - **instruct**: 语音风格指令 (可选)
    - **audio_prompt**: 参考音频 (可选，用于 voice clone)
    - **speed_rate**: 语速倍率 0.5-2.0 (默认 1.0)
    """
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    tts_model = get_model()

    # 检测语言
    detected_lang = (
        normalize_language(language)
        if language and language.lower() != "auto"
        else detect_language(text)
    )
    lang = detected_lang if detected_lang else DEFAULT_LANGUAGE

    print(f"📝 Text: {text[:50]}... | Lang: {lang}")

    audio_prompt_path = None
    temp_files = []

    try:
        # 处理参考音频
        if audio_prompt:
            audio_prompt_path = UPLOAD_DIR / f"{uuid.uuid4()}.wav"
            save_upload_file(audio_prompt, audio_prompt_path)
            temp_files.append(audio_prompt_path)

        # 生成音频
        if audio_prompt_path:
            # 使用 voice clone 方式
            # 创建克隆提示
            clone_prompt = tts_model.create_voice_clone_prompt(
                ref_audio=audio_prompt_path,
                ref_text=None,  # 可选的参考文本
            )

            wavs, sr = tts_model.generate_voice_clone(
                text=text,
                language=lang,
                voice_clone_prompt=clone_prompt,
                instruct=instruct,
                temperature=temperature,
            )
        else:
            # 基础 TTS - Base 模型需要参考音频进行声音克隆
            # 如果没有参考音频，请使用 CustomVoice 或 VoiceDesign 模型
            raise HTTPException(
                status_code=400,
                detail="Base model requires a reference audio for voice cloning. "
                "Please provide an audio_prompt or use a CustomVoice/VoiceDesign model.",
            )

        # 保存输出
        output_path = OUTPUT_DIR / f"{uuid.uuid4()}.wav"

        # 处理音频数据
        if isinstance(wavs, (list, tuple)) and len(wavs) > 0:
            wav = wavs[0]
        else:
            wav = wavs

        if isinstance(wav, torch.Tensor):
            wav = wav.cpu().numpy()

        # 调整语速
        if speed_rate != 1.0:
            wav, sr = adjust_audio_speed(wav, sr, speed_rate)

        sf.write(str(output_path), wav, sr)

        # 设置后台清理
        bg_tasks = BackgroundTasks()
        bg_tasks.add_task(cleanup_file, output_path)
        for f in temp_files:
            bg_tasks.add_task(cleanup_file, f)

        return FileResponse(
            str(output_path),
            media_type="audio/wav",
            filename=f"tts_{lang.lower()}.wav",
            background=bg_tasks,
        )

    except Exception as e:
        import traceback

        err_trace = traceback.format_exc()
        print(f"❌ Error: {err_trace}")
        # 清理临时文件
        for f in temp_files:
            cleanup_file(f)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tts/custom", response_class=FileResponse)
async def tts_custom_voice(
    text: str = Form(...),
    language: Optional[str] = Form("Auto"),
    speaker: str = Form("Ryan"),
    exaggeration: float = Form(DEFAULT_EXAGGERATION),
    temperature: float = Form(DEFAULT_TEMPERATURE),
    instruct: Optional[str] = Form(None),
    speed_rate: float = Form(1.0),
):
    """
    使用预设说话人的文字转语音

    - **text**: 要转换的文本 (必填)
    - **language**: 语言 (默认自动检测)
    - **speaker**: 预设说话人名称 (必填)
    - **exaggeration**: 情感夸张程度 0.0-1.0 (默认 0.5)
    - **temperature**: 采样温度 0.0-1.0 (默认 0.8)
    - **instruct**: 语音风格指令 (可选)
    - **speed_rate**: 语速倍率 0.5-2.0 (默认 1.0)
    """
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    tts_model = get_model()

    # 检测语言
    detected_lang = (
        normalize_language(language)
        if language and language.lower() != "auto"
        else detect_language(text)
    )
    lang = detected_lang if detected_lang else DEFAULT_LANGUAGE

    print(f"📝 Text: {text[:50]}... | Lang: {lang} | Speaker: {speaker}")

    try:
        # 使用预设说话人生成
        wavs, sr = tts_model.generate_custom_voice(
            text=text,
            language=lang,
            speaker=speaker,
            instruct=instruct,
            temperature=temperature,
        )

        # 保存输出
        output_path = OUTPUT_DIR / f"{uuid.uuid4()}.wav"

        # 处理音频数据
        if isinstance(wavs, (list, tuple)) and len(wavs) > 0:
            wav = wavs[0]
        else:
            wav = wavs

        if isinstance(wav, torch.Tensor):
            wav = wav.cpu().numpy()

        # 调整语速
        if speed_rate != 1.0:
            wav, sr = adjust_audio_speed(wav, sr, speed_rate)

        sf.write(str(output_path), wav, sr)

        # 设置后台清理
        bg_tasks = BackgroundTasks()
        bg_tasks.add_task(cleanup_file, output_path)

        return FileResponse(
            str(output_path),
            media_type="audio/wav",
            filename=f"tts_{speaker}_{lang.lower()}.wav",
            background=bg_tasks,
        )

    except Exception as e:
        import traceback

        err_trace = traceback.format_exc()
        print(f"❌ Error: {err_trace}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tts/design", response_class=FileResponse)
async def tts_voice_design(
    text: str = Form(...),
    language: Optional[str] = Form("Auto"),
    instruct: str = Form(...),
    exaggeration: float = Form(DEFAULT_EXAGGERATION),
    temperature: float = Form(DEFAULT_TEMPERATURE),
    speed_rate: float = Form(1.0),
):
    """
    使用自然语言描述生成语音 (Voice Design)

    - **text**: 要转换的文本 (必填)
    - **language**: 语言 (默认自动检测)
    - **instruct**: 自然语言声音描述 (必填)
    - **exaggeration**: 情感夸张程度 0.0-1.0 (默认 0.5)
    - **temperature**: 采样温度 0.0-1.0 (默认 0.8)
    - **speed_rate**: 语速倍率 0.5-2.0 (默认 1.0)
    """
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    if not instruct.strip():
        raise HTTPException(
            status_code=400, detail="Voice description (instruct) cannot be empty"
        )

    tts_model = get_model()

    # 检测语言
    detected_lang = (
        normalize_language(language)
        if language and language.lower() != "auto"
        else detect_language(text)
    )
    lang = detected_lang if detected_lang else DEFAULT_LANGUAGE

    print(f"📝 Text: {text[:50]}... | Lang: {lang} | Instruct: {instruct[:30]}...")

    try:
        # 使用 voice design 生成
        wavs, sr = tts_model.generate_voice_design(
            text=text,
            language=lang,
            instruct=instruct,
            temperature=temperature,
        )

        # 保存输出
        output_path = OUTPUT_DIR / f"{uuid.uuid4()}.wav"

        # 处理音频数据
        if isinstance(wavs, (list, tuple)) and len(wavs) > 0:
            wav = wavs[0]
        else:
            wav = wavs

        if isinstance(wav, torch.Tensor):
            wav = wav.cpu().numpy()

        # 调整语速
        if speed_rate != 1.0:
            wav, sr = adjust_audio_speed(wav, sr, speed_rate)

        sf.write(str(output_path), wav, sr)

        # 设置后台清理
        bg_tasks = BackgroundTasks()
        bg_tasks.add_task(cleanup_file, output_path)

        return FileResponse(
            str(output_path),
            media_type="audio/wav",
            filename=f"tts_design_{lang.lower()}.wav",
            background=bg_tasks,
        )

    except Exception as e:
        import traceback

        err_trace = traceback.format_exc()
        print(f"❌ Error: {err_trace}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tts/clone", response_class=FileResponse)
async def tts_voice_clone(
    text: str = Form(...),
    audio_prompt: UploadFile = File(...),
    language: Optional[str] = Form("Auto"),
    ref_text: Optional[str] = Form(None),
    exaggeration: float = Form(DEFAULT_EXAGGERATION),
    temperature: float = Form(DEFAULT_TEMPERATURE),
    instruct: Optional[str] = Form(None),
    speed_rate: float = Form(1.0),
):
    """
    语音克隆 (Voice Clone)

    - **text**: 要转换的文本 (必填)
    - **audio_prompt**: 参考音频 (必填)
    - **language**: 语言 (默认自动检测)
    - **ref_text**: 参考音频对应的文本 (可选)
    - **exaggeration**: 情感夸张程度 0.0-1.0 (默认 0.5)
    - **temperature**: 采样温度 0.0-1.0 (默认 0.8)
    - **instruct**: 语音风格指令 (可选)
    - **speed_rate**: 语速倍率 0.5-2.0 (默认 1.0)
    """
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    tts_model = get_model()

    # 检测语言
    detected_lang = (
        normalize_language(language)
        if language and language.lower() != "auto"
        else detect_language(text)
    )
    lang = detected_lang if detected_lang else DEFAULT_LANGUAGE

    print(f"📝 Text: {text[:50]}... | Lang: {lang} | Mode: Voice Clone")

    audio_prompt_path = None
    temp_files = []

    try:
        # 保存参考音频
        audio_prompt_path = UPLOAD_DIR / f"{uuid.uuid4()}.wav"
        save_upload_file(audio_prompt, audio_prompt_path)
        temp_files.append(audio_prompt_path)

        # 创建克隆提示
        clone_prompt = tts_model.create_voice_clone_prompt(
            ref_audio=str(audio_prompt_path), ref_text=ref_text
        )

        # 生成克隆语音
        wavs, sr = tts_model.generate_voice_clone(
            text=text,
            language=lang,
            voice_clone_prompt=clone_prompt,
            instruct=instruct,
            temperature=temperature,
        )

        # 保存输出
        output_path = OUTPUT_DIR / f"{uuid.uuid4()}.wav"

        # 处理音频数据
        if isinstance(wavs, (list, tuple)) and len(wavs) > 0:
            wav = wavs[0]
        else:
            wav = wavs

        if isinstance(wav, torch.Tensor):
            wav = wav.cpu().numpy()

        # 调整语速
        if speed_rate != 1.0:
            wav, sr = adjust_audio_speed(wav, sr, speed_rate)

        sf.write(str(output_path), wav, sr)

        # 设置后台清理
        bg_tasks = BackgroundTasks()
        bg_tasks.add_task(cleanup_file, output_path)
        for f in temp_files:
            bg_tasks.add_task(cleanup_file, f)

        return FileResponse(
            str(output_path),
            media_type="audio/wav",
            filename=f"tts_clone_{lang.lower()}.wav",
            background=bg_tasks,
        )

    except Exception as e:
        import traceback

        err_trace = traceback.format_exc()
        print(f"❌ Error: {err_trace}")
        # 清理临时文件
        for f in temp_files:
            cleanup_file(f)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 主程序 ====================
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
