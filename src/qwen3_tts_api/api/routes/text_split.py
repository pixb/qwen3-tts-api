"""
Text Split API Routes
"""
from fastapi import APIRouter

from ...services.text_splitter import split_text
from ...models.text_split import TextSplitRequest, TextSplitResponse


router = APIRouter(prefix="/text", tags=["Text Processing"])


@router.post("/split", response_model=TextSplitResponse)
async def split_long_text(request: TextSplitRequest):
    """
    长文本拆分
    
    将长文本按语义拆分为指定大小的片段，支持中英文。
    
    拆分策略：
    1. 首先按段落拆分
    2. 对于超出大小的段落，按句子拆分
    3. 对于仍然超出大小的句子，尝试按子句拆分
    4. 合并过短的片段
    
    - **text**: 要拆分的长文本 (必填)
    - **max_length**: 单个片段的最大字符数 (默认 200，范围 10-2000)
    - **min_chunk_length**: 合并短片段的最小长度阈值 (默认 50，范围 1-500)
    - **merge_short**: 是否合并过短的片段 (默认 True)
    """
    result = split_text(
        text=request.text,
        max_length=request.max_length,
        min_chunk_length=request.min_chunk_length,
        merge_short=request.merge_short,
    )
    
    return TextSplitResponse(
        success=True,
        chunks=result.chunks,
        chunk_count=result.metadata["chunk_count"],
        original_length=result.metadata["original_length"],
        max_length=result.metadata["max_length"],
    )
