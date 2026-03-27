"""
Resource Path Configuration
"""
from pathlib import Path
from functools import lru_cache


@lru_cache()
def get_project_root() -> Path:
    """获取项目根目录"""
    return Path(__file__).parent.parent.parent.parent


@lru_cache()
def get_data_dir() -> Path:
    """获取数据目录"""
    data_dir = get_project_root() / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir


@lru_cache()
def get_resources_dir() -> Path:
    """获取资源目录"""
    res_dir = get_project_root() / "res"
    res_dir.mkdir(exist_ok=True)
    return res_dir


@lru_cache()
def get_upload_dir() -> Path:
    """获取上传文件目录"""
    upload_dir = get_project_root() / "uploads"
    upload_dir.mkdir(exist_ok=True)
    return upload_dir


@lru_cache()
def get_output_dir() -> Path:
    """获取输出文件目录"""
    output_dir = get_project_root() / "output"
    output_dir.mkdir(exist_ok=True)
    return output_dir


@lru_cache()
def get_references_dir() -> Path:
    """获取参考音频目录"""
    refs_dir = get_resources_dir() / "references"
    refs_dir.mkdir(exist_ok=True)
    return refs_dir


@lru_cache()
def get_custom_audio_dir() -> Path:
    """获取自定义音频目录"""
    custom_dir = get_resources_dir() / "custom_audio"
    custom_dir.mkdir(exist_ok=True)
    return custom_dir


# ==================== Database Paths ====================
@lru_cache()
def get_reference_db_path() -> Path:
    """获取参考音频数据库路径"""
    return get_data_dir() / "tts_references.db"


@lru_cache()
def get_custom_voice_db_path() -> Path:
    """获取自定义音色数据库路径"""
    return get_data_dir() / "tts_custom.db"


@lru_cache()
def get_design_db_path() -> Path:
    """获取语音设计数据库路径"""
    return get_data_dir() / "tts_designs.db"
