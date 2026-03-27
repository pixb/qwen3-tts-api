"""
API Dependencies
"""
from typing import Annotated

from fastapi import Depends, HTTPException

from ..db.reference_store import TTSReferenceStore


def get_reference_store() -> TTSReferenceStore:
    """获取参考音频存储实例"""
    from ..db.reference_store import store as _store
    return _store


# 依赖类型注解
ReferenceStoreDep = Annotated[TTSReferenceStore, Depends(get_reference_store)]
