#!/usr/bin/env python3
"""
初始化示例数据
将 res 目录下的示例音频导入数据库
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.qwen3_tts_api.db.reference_store import store, init_db
from src.qwen3_tts_api.resources.paths import get_references_dir


def init_sample_data():
    """初始化示例数据"""
    # 确保数据库已初始化
    init_db()
    
    references_dir = get_references_dir()
    
    # 示例音频文件
    sample_files = [
        {
            "name": "liuyandong",
            "file_path": "res/liuyandong.mp3",
            "language": "Chinese",
            "description": "中文男声示例",
        },
        {
            "name": "tianyuan",
            "file_path": "res/tianyuan.mp3",
            "language": "Chinese",
            "description": "中文女声示例",
        },
    ]
    
    # 检查是否已有数据
    existing = store.get_all()
    if existing:
        print(f"数据库已有 {len(existing)} 条记录，跳过初始化")
        return
    
    # 导入示例数据
    for sample in sample_files:
        file_path = Path(sample["file_path"])
        if file_path.exists():
            # 复制到 references 目录
            dest_path = references_dir / file_path.name
            if not dest_path.exists():
                import shutil
                shutil.copy(file_path, dest_path)
            
            # 保存到数据库
            reference = store.create(
                name=sample["name"],
                file_path=str(dest_path),
                ref_text=sample.get("description"),
                language=sample["language"],
                exaggeration=0.5,
                temperature=0.8,
                is_default=True if sample == sample_files[0] else False,
            )
            print(f"添加参考音频: {reference['name']} (ID: {reference['id']})")
        else:
            print(f"文件不存在: {file_path}")
    
    print("\n初始化完成!")
    print("\n当前数据库记录:")
    for reference in store.get_all():
        print(f"  - {reference['id']}: {reference['name']} ({reference['language']})")


if __name__ == "__main__":
    init_sample_data()
