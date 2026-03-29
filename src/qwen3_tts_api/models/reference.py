"""
Reference Audio Models
"""
from typing import Optional
from pydantic import BaseModel, Field


class ReferenceAudioCreate(BaseModel):
    """创建参考音频请求"""
    name: str = Field(..., description="音频名称")
    ref_text: str = Field(..., description="参考文本（描述音频内容）")
    language: Optional[str] = Field(None, description="语言")
    exaggeration: float = Field(0.5, ge=0.0, le=1.0, description="情感夸张程度")
    temperature: float = Field(0.8, ge=0.0, le=1.0, description="采样温度")
    instruct: Optional[str] = Field(None, description="语音风格指令")
    speed_rate: float = Field(1.0, ge=0.5, le=2.0, description="语速")
    is_default: bool = Field(False, description="是否设为默认")


class ReferenceAudioUpdate(BaseModel):
    """更新参考音频请求"""
    name: Optional[str] = Field(None, description="新名称")
    ref_text: Optional[str] = Field(None, description="参考文本")
    language: Optional[str] = Field(None, description="语言")
    exaggeration: Optional[float] = Field(None, ge=0.0, le=1.0, description="情感夸张程度")
    temperature: Optional[float] = Field(None, ge=0.0, le=1.0, description="采样温度")
    instruct: Optional[str] = Field(None, description="语音风格指令")
    speed_rate: Optional[float] = Field(None, ge=0.5, le=2.0, description="语速")
    is_default: Optional[bool] = Field(None, description="是否设为默认")


class ReferenceAudioResponse(BaseModel):
    """参考音频响应"""
    id: int
    name: str
    file_path: str
    ref_text: str
    language: Optional[str]
    exaggeration: float
    temperature: float
    instruct: Optional[str]
    speed_rate: float
    is_default: bool
    created_at: str
    updated_at: str
