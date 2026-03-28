"""
TTS Service Module
"""
import uuid
import shutil
import torch
import soundfile as sf
import resampy
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, Union
from fastapi import UploadFile

from ..config import MODEL_NAME, DEFAULT_LANGUAGE, DEFAULT_TEMPERATURE, DEFAULT_EXAGGERATION
from ..resources.paths import get_upload_dir, get_output_dir, get_references_dir


# 全局模型实例
_model = None
_device = None


def get_device() -> str:
    """获取设备"""
    global _device
    if _device is None:
        if torch.cuda.is_available():
            _device = "cuda"
        elif torch.backends.mps.is_available():
            _device = "mps"
        else:
            _device = "cpu"
    return _device


def get_model():
    """
    懒加载模型
    """
    global _model
    if _model is None:
        import qwen_tts
        device = get_device()
        print(f"Loading Qwen3-TTS Model on {device}...")
        
        # 根据设备选择 dtype
        if device == "cuda":
            dtype = torch.bfloat16
        elif device == "mps":
            dtype = torch.float32
        else:
            dtype = torch.float32
        
        _model = qwen_tts.Qwen3TTSModel.from_pretrained(
            MODEL_NAME,
            device_map=device,
            dtype=dtype,
        )
        print(f"Model loaded successfully on {device}")
    return _model


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


def adjust_audio_speed(wav, sr, speed_rate: float) -> Tuple[np.ndarray, int]:
    """
    调整音频速度
    speed_rate: 1.0 = 原始速度, >1.0 = 加速, <1.0 = 减速
    使用重采样方式，会同时改变音调但更稳定
    """
    if speed_rate == 1.0:
        return wav, sr
    
    if wav.dtype != np.float32:
        wav = wav.astype(np.float32)
    
    if wav.max() > 1.0:
        wav = wav / 32768.0
    
    new_sr = int(sr * speed_rate)
    wav_adjusted = resampy.resample(wav, sr_orig=sr, sr_new=new_sr)
    
    return wav_adjusted, new_sr


def generate_with_reference(
    text: str,
    ref_audio_path: str,
    language: str = DEFAULT_LANGUAGE,
    ref_text: Optional[str] = None,
    exaggeration: float = DEFAULT_EXAGGERATION,
    temperature: float = DEFAULT_TEMPERATURE,
    instruct: Optional[str] = None,
    speed_rate: float = 1.0,
) -> Tuple[np.ndarray, int]:
    """
    使用参考音频生成语音
    
    Args:
        text: 要转换的文本
        ref_audio_path: 参考音频路径
        language: 语言
        ref_text: 参考文本
        exaggeration: 情感夸张程度
        temperature: 采样温度
        instruct: 语音风格指令
        speed_rate: 语速
        
    Returns:
        Tuple[audio_data, sample_rate]
    """
    tts_model = get_model()
    
    # 当 ref_text 为空时，使用 x_vector_only_mode（仅声纹，无需文本）
    x_vector_only = not ref_text or not ref_text.strip()
    
    # 创建克隆提示
    clone_prompt = tts_model.create_voice_clone_prompt(
        ref_audio=ref_audio_path,
        ref_text=ref_text if not x_vector_only else None,
        x_vector_only_mode=x_vector_only,
    )
    
    # 生成克隆语音
    wavs, sr = tts_model.generate_voice_clone(
        text=text,
        language=language,
        voice_clone_prompt=clone_prompt,
        instruct=instruct,
        temperature=temperature,
    )
    
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
    
    return wav, sr


def generate_voice_clone(
    text: str,
    audio_prompt_path: str,
    language: str = DEFAULT_LANGUAGE,
    ref_text: Optional[str] = None,
    exaggeration: float = DEFAULT_EXAGGERATION,
    temperature: float = DEFAULT_TEMPERATURE,
    instruct: Optional[str] = None,
    speed_rate: float = 1.0,
) -> Tuple[np.ndarray, int]:
    """
    语音克隆
    
    Args:
        text: 要转换的文本
        audio_prompt_path: 参考音频路径
        language: 语言
        ref_text: 参考音频对应的文本
        exaggeration: 情感夸张程度
        temperature: 采样温度
        instruct: 语音风格指令
        speed_rate: 语速
        
    Returns:
        Tuple[audio_data, sample_rate]
    """
    tts_model = get_model()
    
    # 当 ref_text 为空时，使用 x_vector_only_mode（仅声纹，无需文本）
    x_vector_only = not ref_text or not ref_text.strip()
    
    # 创建克隆提示
    clone_prompt = tts_model.create_voice_clone_prompt(
        ref_audio=audio_prompt_path,
        ref_text=ref_text if not x_vector_only else None,
        x_vector_only_mode=x_vector_only,
    )
    
    # 生成克隆语音
    wavs, sr = tts_model.generate_voice_clone(
        text=text,
        language=language,
        voice_clone_prompt=clone_prompt,
        instruct=instruct,
        temperature=temperature,
    )
    
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
    
    return wav, sr


def generate_voice_design(
    text: str,
    instruct: str,
    language: str = DEFAULT_LANGUAGE,
    exaggeration: float = DEFAULT_EXAGGERATION,
    temperature: float = DEFAULT_TEMPERATURE,
    speed_rate: float = 1.0,
) -> Tuple[np.ndarray, int]:
    """
    语音设计
    
    Args:
        text: 要转换的文本
        instruct: 自然语言声音描述
        language: 语言
        exaggeration: 情感夸张程度
        temperature: 采样温度
        speed_rate: 语速
        
    Returns:
        Tuple[audio_data, sample_rate]
    """
    tts_model = get_model()
    
    # 使用 voice design 生成
    wavs, sr = tts_model.generate_voice_design(
        text=text,
        language=language,
        instruct=instruct,
        temperature=temperature,
    )
    
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
    
    return wav, sr
