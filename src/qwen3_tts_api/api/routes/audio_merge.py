"""
Audio Merge API Routes
"""
import json
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

FADE_IN = 0.05
FADE_OUT = 0.1
GAP_DURATION = 0.1


def get_audio_duration(file_path: Path) -> float:
    """使用 ffprobe 获取音频时长（秒）"""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        str(file_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return 2.0
    try:
        data = json.loads(result.stdout)
        return float(data.get("format", {}).get("duration", 2.0))
    except Exception:
        return 2.0


def generate_silence(output_dir: Path, duration: float = 0.1) -> Path:
    """生成静音音频文件"""
    silence_path = output_dir / f"silence_{uuid.uuid4()}.wav"
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"anullsrc=channel_layout=mono:sample_rate=24000",
        "-t", str(duration),
        str(silence_path)
    ]
    subprocess.run(cmd, capture_output=True, text=True)
    return silence_path


def merge_with_fade(input_paths: List[Path], output_path: Path) -> None:
    """使用 ffmpeg 合并音频，带淡入淡出效果"""
    temp_dir = output_path.parent / f"merge_temp_{uuid.uuid4()}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        durations = [get_audio_duration(p) for p in input_paths]
        
        silence_path = generate_silence(temp_dir, GAP_DURATION)
        processed_paths = []
        
        for i, (in_path, dur) in enumerate(zip(input_paths, durations)):
            fade_out_start = dur - FADE_OUT
            out_path = temp_dir / f"processed_{i}.wav"
            
            cmd = [
                "ffmpeg", "-y", "-i", str(in_path),
                "-af", f"afade=t=in:st=0:d={FADE_IN},afade=t=out:st={fade_out_start}:d={FADE_OUT}",
                str(out_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"ffmpeg fade error: {result.stderr}")
            
            processed_paths.append(out_path)
        
        all_concat_inputs = []
        for i, proc_path in enumerate(processed_paths):
            all_concat_inputs.append(str(proc_path))
            if i < len(processed_paths) - 1:
                all_concat_inputs.append(str(silence_path))
        
        filter_chain = "".join(f"[{i}:a]" for i in range(len(all_concat_inputs)))
        filter_chain += f"concat=n={len(all_concat_inputs)}:v=0:a=1[out]"
        
        cmd = ["ffmpeg", "-y"]
        for inp in all_concat_inputs:
            cmd.extend(["-i", inp])
        cmd.extend(["-filter_complex", filter_chain, "-map", "[out]", str(output_path)])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"ffmpeg concat error: {result.stderr}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


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

        merge_with_fade(input_paths, output_path)

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
