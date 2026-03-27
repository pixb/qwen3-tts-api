"""
Reference Audio Store Module
"""
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from .connection import get_reference_db_connection
from ..resources.paths import get_reference_db_path, get_references_dir


def init_db():
    """初始化数据库和目录"""
    from ..resources.paths import get_reference_db_path, get_references_dir
    
    db_path = get_reference_db_path()
    audio_dir = get_references_dir()
    
    # 确保目录存在
    db_path.parent.mkdir(exist_ok=True)
    audio_dir.mkdir(exist_ok=True)
    
    # 创建表
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tts_references (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            ref_text TEXT,
            language TEXT,
            exaggeration REAL DEFAULT 0.5,
            temperature REAL DEFAULT 0.8,
            instruct TEXT,
            speed_rate REAL DEFAULT 1.0,
            is_default INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()


class TTSReferenceStore:
    """TTS 参考音频存储管理"""
    
    def __init__(self):
        init_db()
    
    def create(
        self,
        name: str,
        file_path: str,
        ref_text: Optional[str] = None,
        language: Optional[str] = None,
        exaggeration: float = 0.5,
        temperature: float = 0.8,
        instruct: Optional[str] = None,
        speed_rate: float = 1.0,
        is_default: bool = False,
    ) -> Dict[str, Any]:
        """创建新的参考音频记录"""
        now = datetime.now().isoformat()
        
        # 如果设为默认音色，先取消其他默认
        if is_default:
            self._clear_default_flags()
        
        with get_reference_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO tts_references (
                    name, file_path, ref_text, language, exaggeration, 
                    temperature, instruct, speed_rate, is_default, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    name,
                    file_path,
                    ref_text,
                    language,
                    exaggeration,
                    temperature,
                    instruct,
                    speed_rate,
                    1 if is_default else 0,
                    now,
                    now,
                ),
            )
            conn.commit()
            reference_id = cursor.lastrowid
        
        return self.get_by_id(reference_id)
    
    def _clear_default_flags(self):
        """清除所有默认参考音频标志"""
        with get_reference_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE tts_references SET is_default = 0")
            conn.commit()
    
    def get_by_id(self, reference_id: int) -> Optional[Dict[str, Any]]:
        """根据 ID 获取参考音频"""
        with get_reference_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM tts_references WHERE id = ?",
                (reference_id,),
            )
            row = cursor.fetchone()
        
        if row:
            return dict(row)
        return None
    
    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """根据名称获取参考音频"""
        with get_reference_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM tts_references WHERE name = ?",
                (name,),
            )
            row = cursor.fetchone()
        
        if row:
            return dict(row)
        return None
    
    def get_all(self) -> List[Dict[str, Any]]:
        """获取所有参考音频"""
        with get_reference_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM tts_references ORDER BY is_default DESC, created_at DESC"
            )
            rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    def get_default(self) -> Optional[Dict[str, Any]]:
        """获取默认参考音频"""
        with get_reference_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM tts_references WHERE is_default = 1 LIMIT 1"
            )
            row = cursor.fetchone()
        
        if row:
            return dict(row)
        return None
    
    def update(
        self,
        reference_id: int,
        name: Optional[str] = None,
        file_path: Optional[str] = None,
        ref_text: Optional[str] = None,
        language: Optional[str] = None,
        exaggeration: Optional[float] = None,
        temperature: Optional[float] = None,
        instruct: Optional[str] = None,
        speed_rate: Optional[float] = None,
        is_default: Optional[bool] = None,
    ) -> Optional[Dict[str, Any]]:
        """更新参考音频"""
        reference = self.get_by_id(reference_id)
        if not reference:
            return None
        
        now = datetime.now()
        
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if file_path is not None:
            updates.append("file_path = ?")
            params.append(file_path)
        if ref_text is not None:
            updates.append("ref_text = ?")
            params.append(ref_text)
        if language is not None:
            updates.append("language = ?")
            params.append(language)
        if exaggeration is not None:
            updates.append("exaggeration = ?")
            params.append(exaggeration)
        if temperature is not None:
            updates.append("temperature = ?")
            params.append(temperature)
        if instruct is not None:
            updates.append("instruct = ?")
            params.append(instruct)
        if speed_rate is not None:
            updates.append("speed_rate = ?")
            params.append(speed_rate)
        if is_default is not None:
            if is_default:
                self._clear_default_flags()
            updates.append("is_default = ?")
            params.append(1 if is_default else 0)
        
        updates.append("updated_at = ?")
        params.append(now.isoformat())
        params.append(reference_id)
        
        with get_reference_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE tts_references SET {', '.join(updates)} WHERE id = ?",
                params,
            )
            conn.commit()
        
        return self.get_by_id(reference_id)
    
    def delete(self, reference_id: int) -> bool:
        """删除参考音频"""
        reference = self.get_by_id(reference_id)
        if not reference:
            return False
        
        # 删除文件（支持相对路径和绝对路径，向后兼容）
        stored_path = reference["file_path"]
        if Path(stored_path).is_absolute():
            file_path = Path(stored_path)
        else:
            file_path = get_references_dir() / stored_path
        
        if file_path.exists():
            file_path.unlink()
        
        # 删除数据库记录
        with get_reference_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM tts_references WHERE id = ?",
                (reference_id,),
            )
            conn.commit()
        
        return True


# 全局实例
store = TTSReferenceStore()
