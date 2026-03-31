"""
Text Split Models
"""
from typing import List
from pydantic import BaseModel, Field


class TextSplitRequest(BaseModel):
    """文本拆分请求"""
    text: str = Field(..., min_length=1, description="要拆分的长文本")
    max_length: int = Field(100, ge=10, le=2000, description="单个片段的最大字符数")
    min_chunk_length: int = Field(50, ge=1, le=500, description="合并短片段的最小长度阈值")
    merge_short: bool = Field(True, description="是否合并过短的片段")


class TextSplitResponse(BaseModel):
    """文本拆分响应"""
    success: bool = Field(True, description="是否成功")
    chunks: List[str] = Field(..., description="拆分后的文本片段列表")
    chunk_count: int = Field(..., description="片段数量")
    original_length: int = Field(..., description="原始文本长度")
    max_length: int = Field(..., description="单个片段的最大字符数")
