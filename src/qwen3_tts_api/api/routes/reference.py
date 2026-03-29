"""
Reference Audio API Routes
"""
import uuid
import shutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse

from ...db.reference_store import store
from ...resources.paths import get_references_dir


router = APIRouter(prefix="/tts/reference", tags=["Reference Audio Management"])


# 支持的音频格式
ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac"}


def validate_audio_file(filename: str) -> bool:
    """验证音频文件格式"""
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_AUDIO_EXTENSIONS


@router.post("/upload")
async def upload_reference_audio(
    name: str = Form(...),
    file: UploadFile = File(...),
    ref_text: str = Form(...),
    language: Optional[str] = Form(None),
    exaggeration: Optional[float] = Form(0.5),
    temperature: Optional[float] = Form(0.8),
    instruct: Optional[str] = Form(None),
    speed_rate: Optional[float] = Form(1.0),
    is_default: bool = Form(False),
):
    """
    上传参考音频
    
    - **name**: 音频名称 (必填)
    - **file**: 音频文件 (必填，支持 mp3/wav/m4a/flac/ogg/aac)
    - **ref_text**: 参考文本（必填，描述音频内容）
    - **language**: 语言 (可选)
    - **exaggeration**: 默认情感夸张值 0.0-1.0 (默认 0.5)
    - **temperature**: 默认采样温度 0.0-1.0 (默认 0.8)
    - **instruct**: 默认语音风格指令 (可选)
    - **speed_rate**: 默认语速 0.5-2.0 (默认 1.0)
    - **is_default**: 是否设为默认参考音频 (默认 False)
    """
    # 验证 ref_text 不为空
    if not ref_text.strip():
        raise HTTPException(
            status_code=400,
            detail="ref_text 不能为空",
        )
    
    # 验证文件类型
    if not validate_audio_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"不支持的音频格式。支持: {', '.join(ALLOWED_AUDIO_EXTENSIONS)}",
        )
    
    # 检查名称是否已存在
    existing = store.get_by_name(name.strip())
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"名称 '{name}' 已存在，请使用其他名称",
        )
    
    # 生成唯一文件名
    audio_dir = get_references_dir()
    file_ext = Path(file.filename).suffix.lower()
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = audio_dir / unique_filename
    
    # 保存文件
    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存文件失败: {str(e)}")
    
    # 保存到数据库（使用相对于项目根的路径，便于迁移）
    relative_path = str(file_path.relative_to(get_references_dir()))
    try:
        reference = store.create(
            name=name.strip(),
            file_path=relative_path,
            ref_text=ref_text,
            language=language,
            exaggeration=exaggeration or 0.5,
            temperature=temperature or 0.8,
            instruct=instruct,
            speed_rate=speed_rate or 1.0,
            is_default=is_default,
        )
    except Exception as e:
        # 删除已保存的文件
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"保存记录失败: {str(e)}")
    
    return {
        "success": True,
        "message": "参考音频上传成功",
        "data": reference,
    }


@router.get("/list")
async def list_references():
    """
    列出所有参考音频
    """
    references = store.get_all()
    return {
        "success": True,
        "total": len(references),
        "data": references,
    }


@router.get("/default")
async def get_default_reference():
    """
    获取默认参考音频
    """
    reference = store.get_default()
    if not reference:
        raise HTTPException(status_code=404, detail="未设置默认参考音频")
    
    return {
        "success": True,
        "data": reference,
    }


@router.post("/default/{reference_id}")
async def set_default_reference(reference_id: int):
    """
    设置默认参考音频
    
    - **reference_id**: 参考音频 ID
    """
    reference = store.update(reference_id=reference_id, is_default=True)
    
    if not reference:
        raise HTTPException(status_code=404, detail="参考音频不存在")
    
    return {
        "success": True,
        "message": "默认参考音频设置成功",
        "data": reference,
    }


@router.get("/{reference_id}")
async def get_reference(reference_id: int):
    """
    获取单个参考音频详情
    
    - **reference_id**: 参考音频 ID
    """
    reference = store.get_by_id(reference_id)
    if not reference:
        raise HTTPException(status_code=404, detail="参考音频不存在")
    
    return {
        "success": True,
        "data": reference,
    }


@router.get("/{reference_id}/audio")
async def download_reference_audio(reference_id: int):
    """
    下载参考音频文件
    
    - **reference_id**: 参考音频 ID
    """
    reference = store.get_by_id(reference_id)
    if not reference:
        raise HTTPException(status_code=404, detail="参考音频不存在")
    
    # 支持相对路径和绝对路径（向后兼容）
    stored_path = reference["file_path"]
    if Path(stored_path).is_absolute():
        file_path = Path(stored_path)
    else:
        file_path = get_references_dir() / stored_path
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="音频文件不存在")
    
    return FileResponse(
        path=str(file_path),
        filename=reference["name"] + Path(reference["file_path"]).suffix,
        media_type="audio/mpeg",
    )


@router.post("/{reference_id}")
async def update_reference(
    reference_id: int,
    name: Optional[str] = Form(None),
    ref_text: Optional[str] = Form(None),
    language: Optional[str] = Form(None),
    exaggeration: Optional[float] = Form(None),
    temperature: Optional[float] = Form(None),
    instruct: Optional[str] = Form(None),
    speed_rate: Optional[float] = Form(None),
    is_default: Optional[bool] = Form(None),
):
    """
    更新参考音频
    
    - **reference_id**: 参考音频 ID
    - **name**: 新名称 (可选)
    - **ref_text**: 参考文本 (可选)
    - **language**: 语言 (可选)
    - **exaggeration**: 情感夸张值 0.0-1.0 (可选)
    - **temperature**: 采样温度 0.0-1.0 (可选)
    - **instruct**: 语音风格指令 (可选)
    - **speed_rate**: 语速 0.5-2.0 (可选)
    - **is_default**: 是否设为默认 (可选)
    """
    # 检查名称是否已存在（如果是更新名称）
    if name:
        existing = store.get_by_name(name.strip())
        if existing and existing["id"] != reference_id:
            raise HTTPException(
                status_code=400,
                detail=f"名称 '{name}' 已存在，请使用其他名称",
            )
    
    reference = store.update(
        reference_id=reference_id,
        name=name.strip() if name else None,
        ref_text=ref_text,
        language=language,
        exaggeration=exaggeration,
        temperature=temperature,
        instruct=instruct,
        speed_rate=speed_rate,
        is_default=is_default,
    )
    
    if not reference:
        raise HTTPException(status_code=404, detail="参考音频不存在")
    
    return {
        "success": True,
        "message": "参考音频更新成功",
        "data": reference,
    }


@router.delete("/{reference_id}")
async def delete_reference(reference_id: int):
    """
    删除参考音频
    
    - **reference_id**: 参考音频 ID
    """
    success = store.delete(reference_id)
    if not success:
        raise HTTPException(status_code=404, detail="参考音频不存在")
    
    return {
        "success": True,
        "message": "参考音频删除成功",
    }
