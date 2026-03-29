"""
TTS Service Module
"""
import uuid
import shutil
import time
import threading
import torch
import soundfile as sf
import resampy
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, Union
from fastapi import UploadFile

from ..config import MODEL_NAME, DEFAULT_LANGUAGE, DEFAULT_TEMPERATURE, DEFAULT_EXAGGERATION
from ..resources.paths import get_upload_dir, get_output_dir, get_references_dir


_model = None
_device = None
_last_used_time = None

IDLE_TIMEOUT_SECONDS = 1800


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
    global _model, _last_used_time
    _last_used_time = time.time()
    if _model is None:
        import qwen_tts
        device = get_device()
        print(f"Loading Qwen3-TTS Model on {device}...")
        
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


def unload_model_if_idle():
    """
    空闲时卸载模型释放显存
    返回 True 表示已卸载，False 表示模型仍在使用或未加载
    """
    global _model, _last_used_time
    if _model is None:
        return False
    if _last_used_time is None:
        return False
    if time.time() - _last_used_time > IDLE_TIMEOUT_SECONDS:
        print("[Memory] Unloading idle model to free memory...")
        del _model
        _model = None
        _last_used_time = None
        _cleanup_generation_memory()
        print("[Memory] Model unloaded successfully")
        return True
    return False


def get_model_status():
    """获取模型状态信息"""
    global _model, _last_used_time
    if _model is None:
        return {"loaded": False, "idle_seconds": None}
    idle_seconds = time.time() - _last_used_time if _last_used_time else 0
    return {
        "loaded": True,
        "idle_seconds": int(idle_seconds),
        "will_unload_in": max(0, int(IDLE_TIMEOUT_SECONDS - idle_seconds))
    }


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
    
    try:
        x_vector_only = not ref_text or not ref_text.strip()
        
        with torch.inference_mode():
            clone_prompt = tts_model.create_voice_clone_prompt(
                ref_audio=ref_audio_path,
                ref_text=ref_text if not x_vector_only else None,
                x_vector_only_mode=x_vector_only,
            )
            
            wavs, sr = tts_model.generate_voice_clone(
                text=text,
                language=language,
                voice_clone_prompt=clone_prompt,
                instruct=instruct,
                temperature=temperature,
            )
        
        if isinstance(wavs, (list, tuple)) and len(wavs) > 0:
            wav = wavs[0]
        else:
            wav = wavs
        
        if isinstance(wav, torch.Tensor):
            wav = wav.cpu().numpy()
        
        if speed_rate != 1.0:
            wav, sr = adjust_audio_speed(wav, sr, speed_rate)
        
        del clone_prompt, wavs
        
        return wav, sr
    
    finally:
        _cleanup_generation_memory()


def _cleanup_generation_memory():
    """清理生成过程中的临时内存"""
    import gc
    import time
    
    gc.collect()
    time.sleep(0.1)
    gc.collect()
    time.sleep(0.1)
    gc.collect()
    time.sleep(0.1)
    
    device = get_device()
    if device == "cuda":
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
    elif device == "mps":
        torch.mps.empty_cache()
        time.sleep(0.2)
        torch.mps.empty_cache()
        time.sleep(0.2)
        torch.mps.empty_cache()


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
    
    try:
        x_vector_only = not ref_text or not ref_text.strip()
        
        with torch.inference_mode():
            clone_prompt = tts_model.create_voice_clone_prompt(
                ref_audio=audio_prompt_path,
                ref_text=ref_text if not x_vector_only else None,
                x_vector_only_mode=x_vector_only,
            )
            
            wavs, sr = tts_model.generate_voice_clone(
                text=text,
                language=language,
                voice_clone_prompt=clone_prompt,
                instruct=instruct,
                temperature=temperature,
            )
        
        if isinstance(wavs, (list, tuple)) and len(wavs) > 0:
            wav = wavs[0]
        else:
            wav = wavs
        
        if isinstance(wav, torch.Tensor):
            wav = wav.cpu().numpy()
        
        if speed_rate != 1.0:
            wav, sr = adjust_audio_speed(wav, sr, speed_rate)
        
        del clone_prompt, wavs
        
        return wav, sr
    
    finally:
        _cleanup_generation_memory()


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
    
    try:
        with torch.inference_mode():
            wavs, sr = tts_model.generate_voice_design(
                text=text,
                language=language,
                instruct=instruct,
                temperature=temperature,
            )
        
        if isinstance(wavs, (list, tuple)) and len(wavs) > 0:
            wav = wavs[0]
        else:
            wav = wavs
        
        if isinstance(wav, torch.Tensor):
            wav = wav.cpu().numpy()
        
        if speed_rate != 1.0:
            wav, sr = adjust_audio_speed(wav, sr, speed_rate)
        
        del wavs
        
        return wav, sr
    
    finally:
        _cleanup_generation_memory()



