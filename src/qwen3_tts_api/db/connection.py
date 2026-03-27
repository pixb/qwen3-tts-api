"""
Database Connection Module
"""
import sqlite3
from contextlib import contextmanager
from typing import Generator

from ..resources.paths import get_reference_db_path


def get_reference_db_path() -> str:
    """获取参考音频数据库路径"""
    from ..resources.paths import get_reference_db_path as _get_path
    return str(_get_path())


@contextmanager
def get_db_connection(db_path: str) -> Generator[sqlite3.Connection, None, None]:
    """
    获取数据库连接
    
    Args:
        db_path: 数据库文件路径
        
    Yields:
        sqlite3.Connection: 数据库连接
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def get_reference_db_connection():
    """获取参考音频数据库连接"""
    with get_db_connection(get_reference_db_path()) as conn:
        yield conn
