"""
Qwen3-TTS FastAPI Server Main Entry
"""
import uuid
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from .config import (
    DEFAULT_LANGUAGE,
    DEFAULT_TEMPERATURE,
    DEFAULT_EXAGGERATION,
    SUPPORTED_LANGUAGES,
)
from .services.utils import detect_language, normalize_language, cleanup_file
from .services import tts as tts_service
from .resources.paths import get_upload_dir, get_output_dir, get_references_dir
from .api.routes.reference import router as reference_router


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

# 注册路由
app.include_router(reference_router)

# ==================== 目录初始化 ====================
UPLOAD_DIR = get_upload_dir()
OUTPUT_DIR = get_output_dir()


# ==================== 健康检查 ====================
@app.get("/health")
async def health_check():
    """健康检查端点"""
    device = tts_service.get_device()
    return {
        "status": "healthy",
        "device": device,
        "model": "Qwen/Qwen3-TTS-12Hz-0.6B-Base",
        "supported_languages": SUPPORTED_LANGUAGES,
    }


@app.get("/languages")
async def get_languages():
    """获取支持的语言列表"""
    return {"languages": SUPPORTED_LANGUAGES, "default": DEFAULT_LANGUAGE}


# ==================== TTS 端点 ====================

@app.post("/tts/custom", response_class=FileResponse)
async def tts_custom_voice(
    text: str = Form(...),
    language: Optional[str] = Form("Auto"),
    speaker: str = Form("Ryan"),
    use_custom: bool = Form(False),
    exaggeration: float = Form(DEFAULT_EXAGGERATION),
    temperature: float = Form(DEFAULT_TEMPERATURE),
    instruct: Optional[str] = Form(None),
    speed_rate: float = Form(1.0),
):
    """
    使用预设说话人的文字转语音
    
    - **text**: 要转换的文本 (必填)
    - **language**: 语言 (默认自动检测)
    - **speaker**: 预设说话人名称 或 自定义音色标识符 (必填)
    - **use_custom**: 是否使用自定义预设音色 (默认 False)
    - **exaggeration**: 情感夸张程度 0.0-1.0 (默认 0.5)
    - **temperature**: 采样温度 0.0-1.0 (默认 0.8)
    - **instruct**: 语音风格指令 (可选)
    - **speed_rate**: 语速倍率 0.5-2.0 (默认 1.0)
    """
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    # 检测语言
    detected_lang = (
        normalize_language(language)
        if language and language.lower() != "auto"
        else detect_language(text)
    )
    lang = detected_lang if detected_lang else DEFAULT_LANGUAGE
    
    print(f"📝 Text: {text[:50]}... | Lang: {lang} | Speaker: {speaker} | Use Custom: {use_custom}")
    
    # 注意：自定义音色功能需要实现 TTSCustomVoiceStore
    # 目前使用占位逻辑，后续可以添加
    if use_custom:
        raise HTTPException(
            status_code=501,
            detail="自定义预设音色功能尚未实现，请使用预设说话人",
        )
    
    temp_files = []
    
    try:
        # 使用预设说话人生成
        wav, sr = tts_service.generate_custom_voice(
            text=text,
            speaker=speaker,
            language=lang,
            exaggeration=exaggeration,
            temperature=temperature,
            instruct=instruct,
            speed_rate=speed_rate,
        )
        
        # 保存输出
        output_path = OUTPUT_DIR / f"{uuid.uuid4()}.wav"
        tts_service.save_audio([wav], sr, output_path)
        
        # 设置后台清理
        bg_tasks = BackgroundTasks()
        bg_tasks.add_task(cleanup_file, output_path)
        
        return FileResponse(
            str(output_path),
            media_type="audio/wav",
            filename=f"tts_{speaker}_{lang.lower()}.wav",
            background=bg_tasks,
        )
    
    except HTTPException:
        raise
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
        wav, sr = tts_service.generate_voice_design(
            text=text,
            instruct=instruct,
            language=lang,
            exaggeration=exaggeration,
            temperature=temperature,
            speed_rate=speed_rate,
        )
        
        # 保存输出
        output_path = OUTPUT_DIR / f"{uuid.uuid4()}.wav"
        tts_service.save_audio([wav], sr, output_path)
        
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
        tts_service.save_upload_file(audio_prompt, audio_prompt_path)
        temp_files.append(audio_prompt_path)
        
        # 生成克隆语音
        wav, sr = tts_service.generate_voice_clone(
            text=text,
            audio_prompt_path=str(audio_prompt_path),
            language=lang,
            ref_text=ref_text,
            exaggeration=exaggeration,
            temperature=temperature,
            instruct=instruct,
            speed_rate=speed_rate,
        )
        
        # 保存输出
        output_path = OUTPUT_DIR / f"{uuid.uuid4()}.wav"
        tts_service.save_audio([wav], sr, output_path)
        
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


@app.post("/tts/generate", response_class=FileResponse)
async def tts_generate_with_reference(
    text: str = Form(default=""),
    reference_id: Optional[int] = Form(None),
    reference_name: Optional[str] = Form(None),
    language: Optional[str] = Form("Auto"),
    ref_text: Optional[str] = Form(None),
    exaggeration: Optional[float] = Form(None),
    temperature: Optional[float] = Form(None),
    instruct: Optional[str] = Form(None),
    speed_rate: Optional[float] = Form(None),
):
    """
    使用保存的参考音频生成语音
    
    - **text**: 要转换的文本 (必填)
    - **reference_id**: 参考音频 ID (必填，至少提供 reference_id 或 reference_name 之一)
    - **reference_name**: 参考音频名称 (必填，至少提供 reference_id 或 reference_name 之一)
    - **language**: 语言 (默认自动检测)
    - **ref_text**: 参考文本，会覆盖保存的默认值 (可选)
    - **exaggeration**: 情感夸张程度 0.0-1.0，会覆盖保存的默认值 (可选)
    - **temperature**: 采样温度 0.0-1.0，会覆盖保存的默认值 (可选)
    - **instruct**: 语音风格指令，会覆盖保存的默认值 (可选)
    - **speed_rate**: 语速倍率 0.5-2.0，会覆盖保存的默认值 (可选)
    """
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    # 检查参数
    if not reference_id and not reference_name:
        raise HTTPException(
            status_code=400,
            detail="必须提供 reference_id 或 reference_name 之一",
        )
    
    # 导入参考音频存储
    from .db.reference_store import store as reference_store
    
    # 检测语言
    detected_lang = (
        normalize_language(language)
        if language and language.lower() != "auto"
        else detect_language(text)
    )
    lang = detected_lang if detected_lang else DEFAULT_LANGUAGE
    
    temp_files = []
    
    try:
        # 获取参考音频
        reference = None
        if reference_id:
            reference = reference_store.get_by_id(reference_id)
        elif reference_name:
            reference = reference_store.get_by_name(reference_name)
        
        if not reference:
            raise HTTPException(
                status_code=404,
                detail=f"未找到参考音频 (id: {reference_id}, name: {reference_name})",
            )
        
        # 获取参考音频路径（支持相对路径和绝对路径，向后兼容）
        stored_path = reference["file_path"]
        if Path(stored_path).is_absolute():
            ref_audio_path = Path(stored_path)
        else:
            ref_audio_path = get_references_dir() / stored_path
        
        if not ref_audio_path.exists():
            raise HTTPException(status_code=404, detail="参考音频文件不存在")
        
        temp_files.append(ref_audio_path)
        
        # 使用覆盖参数或默认值
        use_ref_text = ref_text if ref_text is not None else reference.get("ref_text")
        use_exaggeration = exaggeration if exaggeration is not None else reference.get("exaggeration", DEFAULT_EXAGGERATION)
        use_temperature = temperature if temperature is not None else reference.get("temperature", DEFAULT_TEMPERATURE)
        use_instruct = instruct if instruct is not None else reference.get("instruct")
        use_speed_rate = speed_rate if speed_rate is not None else reference.get("speed_rate", 1.0)
        
        print(f"📝 Text: {text[:50]}... | Lang: {lang} | Reference: {reference['name']}")
        print(f"   Params: exaggeration={use_exaggeration}, temperature={use_temperature}, instruct={use_instruct}, speed_rate={use_speed_rate}")
        
        # 生成克隆语音
        wav, sr = tts_service.generate_with_reference(
            text=text,
            ref_audio_path=str(ref_audio_path),
            language=lang,
            ref_text=use_ref_text,
            exaggeration=use_exaggeration,
            temperature=use_temperature,
            instruct=use_instruct,
            speed_rate=use_speed_rate,
        )
        
        # 保存输出
        output_path = OUTPUT_DIR / f"{uuid.uuid4()}.wav"
        tts_service.save_audio([wav], sr, output_path)
        
        # 设置后台清理
        bg_tasks = BackgroundTasks()
        bg_tasks.add_task(cleanup_file, output_path)
        
        return FileResponse(
            str(output_path),
            media_type="audio/wav",
            filename=f"tts_{reference['name']}_{lang.lower()}.wav",
            background=bg_tasks,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        err_trace = traceback.format_exc()
        print(f"❌ Error: {err_trace}")
        raise HTTPException(status_code=500, detail=str(e))
