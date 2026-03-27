"""
Utility Functions
"""
import re
from typing import Optional
from pathlib import Path

from ..config import LANGUAGE_CODE_MAP


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


def normalize_language(language: Optional[str]) -> Optional[str]:
    """
    标准化语言参数
    """
    if not language or language.lower() == "auto":
        return None  # 返回 None 表示自动检测
    
    lang_lower = language.lower().strip()
    return LANGUAGE_CODE_MAP.get(lang_lower, language.capitalize())


def cleanup_file(path: Path) -> None:
    """清理单个文件"""
    if path and path.exists():
        try:
            path.unlink()
            print(f"Cleaned up: {path}")
        except Exception as e:
            print(f"Cleanup error: {e}")
