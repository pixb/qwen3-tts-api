import pytest
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 导入配置
BASE_URL = "http://localhost:8001"


@pytest.fixture
def base_url():
    return BASE_URL


@pytest.fixture
def reference_audio_path():
    """参考音频文件路径"""
    return "output.wav"
