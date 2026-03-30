"""
Audio Merge API Routes
"""
import subprocess
import uuid
import shutil
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

from ...resources.paths import get_output_dir


router = APIRouter(prefix="/audio", tags=["Audio Processing"])


@router.post("/merge")
async def merge_audio_files(files: List[UploadFile] = File(...)):
    """
    合并多个音频文件
    
    使用 ffmpeg concat 合并多个 WAV 音频文件为单个音频。
    
    - **files**: 要合并的音频文件列表 (至少2个，必填，支持 wav/mp3/m4a/flac/ogg/aac)
    """
    if len(files) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least 2 audio files are required for merging"
        )

    output_dir = get_output_dir()
    temp_dir = output_dir / f"merge_temp_{uuid.uuid4()}"
    temp_dir.mkdir(parents=True, exist_ok=True)

    try:
        input_paths = []
        for i, file in enumerate(files):
            ext = Path(file.filename).suffix.lower()
            if ext not in [".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aac"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported audio format: {ext}"
                )
            
            temp_path = temp_dir / f"input_{i}{ext}"
            with open(temp_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
            input_paths.append(temp_path)

        output_filename = f"merged_{datetime.now().strftime('%Y%m%d-%H%M%S')}.wav"
        output_path = output_dir / output_filename

        cmd = ["ffmpeg", "-y"]
        for p in input_paths:
            cmd.extend(["-i", str(p)])
        
        filter_complex = "".join(
            f"[{i}:a]" for i in range(len(input_paths))
        )
        filter_complex += f"concat=n={len(input_paths)}:v=0:a=1"
        
        cmd.extend(["-filter_complex", filter_complex, str(output_path)])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to merge audio files: {result.stderr}"
            )

        return FileResponse(
            path=output_path,
            media_type="audio/wav",
            filename=output_filename,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error merging audio files: {str(e)}"
        )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@router.post("/upload")
async def upload_audio(file: UploadFile = File(...)):
    """
    上传音频文件到服务器
    
    - **file**: 要上传的音频文件 (支持 wav/mp3/m4a/flac/ogg/aac)
    
    返回可访问的音频 URL
    """
    ext = Path(file.filename).suffix.lower() if file.filename else ".wav"
    if ext not in [".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aac"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format: {ext}"
        )

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{timestamp}{ext}"
    output_path = get_output_dir() / filename

    try:
        with open(output_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        file_size = output_path.stat().st_size
        
        return {
            "success": True,
            "filename": filename,
            "url": f"/audio/{filename}",
            "size": file_size
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading audio: {str(e)}"
        )
