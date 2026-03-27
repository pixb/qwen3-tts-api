"""
数据库迁移脚本
将 tts_designs 和 tts_custom_voices 表的数据迁移到 tts_references 表
"""

import sqlite3
from pathlib import Path
from datetime import datetime


# 数据库路径
OLD_DB_PATHS = [
    Path("data") / "tts_designs.db",
    Path("data") / "tts_custom.db",
]
NEW_DB_PATH = Path("data") / "tts_references.db"


def migrate():
    """执行数据迁移"""
    if not NEW_DB_PATH.exists():
        print("新数据库不存在，请先运行程序创建新数据库")
        return False

    # 连接新数据库
    conn = sqlite3.connect(NEW_DB_PATH)
    cursor = conn.cursor()

    total_migrated = 0

    # 遍历旧数据库
    for old_db_path in OLD_DB_PATHS:
        if not old_db_path.exists():
            print(f"旧数据库不存在: {old_db_path}")
            continue

        print(f"\n正在迁移: {old_db_path}")

        old_conn = sqlite3.connect(old_db_path)
        old_conn.row_factory = sqlite3.Row
        old_cursor = old_conn.cursor()

        # 判断旧数据库类型
        table_name = None
        if "tts_designs" in str(old_db_path):
            table_name = "tts_designs"
        elif "tts_custom" in str(old_db_path):
            table_name = "tts_custom_voices"

        if not table_name:
            old_conn.close()
            continue

        # 获取旧数据
        old_cursor.execute(f"SELECT * FROM {table_name}")
        rows = old_cursor.fetchall()

        print(f"  找到 {len(rows)} 条记录")

        for row in rows:
            try:
                if table_name == "tts_designs":
                    # tts_designs 表字段映射
                    # id, name, file_path, language, description, created_at, updated_at
                    cursor.execute(
                        """
                        INSERT INTO tts_references (
                            name, file_path, ref_text, language, 
                            exaggeration, temperature, instruct, speed_rate,
                            is_default, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            row["name"],
                            row["file_path"],
                            row.get("description"),  # 旧表没有 ref_text，用 description
                            row.get("language"),
                            0.5,  # 默认值
                            0.8,  # 默认值
                            None,  # 默认值
                            1.0,  # 默认值
                            0,  # 默认值
                            row.get("created_at"),
                            row.get("updated_at"),
                        ),
                    )
                elif table_name == "tts_custom_voices":
                    # tts_custom_voices 表字段映射
                    # id, name, speaker, file_path, language, description, is_default, created_at, updated_at
                    cursor.execute(
                        """
                        INSERT INTO tts_references (
                            name, file_path, ref_text, language, 
                            exaggeration, temperature, instruct, speed_rate,
                            is_default, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            f"{row['name']} ({row['speaker']})",  # 合并名称和说话人
                            row["file_path"],
                            row.get("description"),  # 旧表没有 ref_text，用 description
                            row.get("language"),
                            0.5,  # 默认值
                            0.8,  # 默认值
                            None,  # 默认值
                            1.0,  # 默认值
                            row.get("is_default", 0),
                            row.get("created_at"),
                            row.get("updated_at"),
                        ),
                    )

                total_migrated += 1
                print(f"  ✓ 迁移: {row['name']}")

            except Exception as e:
                print(f"  ✗ 迁移失败: {row.get('name', 'unknown')} - {e}")

        old_conn.close()

    conn.commit()
    conn.close()

    print(f"\n✅ 迁移完成，共迁移 {total_migrated} 条记录")
    return True


if __name__ == "__main__":
    migrate()
