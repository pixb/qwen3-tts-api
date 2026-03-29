import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from qwen3_tts_api.main import app


client = TestClient(app)


class TestTextSplitAPI:
    """长文本拆分API测试"""

    def test_split_basic(self):
        """基本拆分测试"""
        payload = {
            "text": "这是一个测试文本。我们希望将它拆分成小于200个字符的片段。这是一段很长的文字，用于测试当段落超过最大长度时的处理情况。",
            "max_length": 50,
        }

        response = client.post("/text/split", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["chunk_count"] > 0
        assert len(data["chunks"]) > 0
        assert data["original_length"] > 0
        assert data["max_length"] == 50
        for chunk in data["chunks"]:
            assert len(chunk) <= 50

    def test_split_chinese(self):
        """中文拆分测试"""
        payload = {
            "text": "这是一个测试文本。我们希望将它拆分成小于20个字符的片段。这是一段很长的文字，用于测试当段落超过最大长度时的处理情况。",
            "max_length": 20,
        }

        response = client.post("/text/split", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["chunk_count"] > 1
        for chunk in data["chunks"]:
            assert len(chunk) <= 20

    def test_split_english(self):
        """英文拆分测试"""
        payload = {
            "text": "This is a test text. We want to split it into chunks of less than 50 characters.",
            "max_length": 30,
        }

        response = client.post("/text/split", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["chunk_count"] > 0
        for chunk in data["chunks"]:
            assert len(chunk) <= 30

    def test_split_empty_text(self):
        """空文本测试"""
        payload = {"text": ""}

        response = client.post("/text/split", json=payload)

        # Pydantic validation should reject empty text
        assert response.status_code == 422

    def test_split_multiple_paragraphs(self):
        """多段落拆分测试"""
        payload = {
            "text": """这是第一段内容。我们在这里测试多段落的拆分功能。

这是第二段内容。它包含更多的内容，用于测试拆分功能。

这里是第三段。我们继续添加更多的内容，以确保测试的准确性。这是一段很长的文字，用于测试当段落超过最大长度时的处理情况。""",
            "max_length": 50,
        }

        response = client.post("/text/split", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["chunk_count"] > 0
        for chunk in data["chunks"]:
            assert len(chunk) <= 50

    def test_split_no_merge(self):
        """不合并短片段测试"""
        payload = {
            "text": "这是第一句。这是第二句。这是一句很短的句子。",
            "max_length": 50,
            "merge_short": False,
        }

        response = client.post("/text/split", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["chunks"]) > 0

    def test_split_custom_min_length(self):
        """自定义最小片段长度测试"""
        payload = {
            "text": "短。句子。测试。",
            "max_length": 50,
            "min_chunk_length": 10,
            "merge_short": True,
        }

        response = client.post("/text/split", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["chunk_count"] > 0

    def test_split_long_sentence(self):
        """超长句子拆分测试"""
        payload = {
            "text": "这是一段非常非常长的文字，用于测试当单个句子就超过最大长度时的处理情况。我们需要在适当的位置进行拆分，同时保持语义的完整性。",
            "max_length": 30,
        }

        response = client.post("/text/split", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["chunk_count"] > 1
        for chunk in data["chunks"]:
            assert len(chunk) <= 30

    def test_split_mixed_language(self):
        """中英混合拆分测试"""
        payload = {
            "text": "你好，这是一个测试。Hello, this is a test. 我们来测试混合语言的拆分。",
            "max_length": 30,
        }

        response = client.post("/text/split", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["chunk_count"] > 0

    def test_split_default_params(self):
        """使用默认参数测试"""
        payload = {
            "text": "这是一个测试文本。我们希望将它拆分成默认大小的片段。这是一段很长的文字，用于测试当段落超过最大长度时的处理情况。",
        }

        response = client.post("/text/split", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["max_length"] == 200
        assert data["chunk_count"] > 0

    def test_split_invalid_max_length(self):
        """无效的max_length参数测试"""
        payload = {
            "text": "测试文本",
            "max_length": 5,  # 小于最小值10
        }

        response = client.post("/text/split", json=payload)

        # Pydantic validation should reject invalid max_length
        assert response.status_code == 422

    def test_split_response_format(self):
        """响应格式测试"""
        payload = {"text": "测试文本"}

        response = client.post("/text/split", json=payload)

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")
        data = response.json()
        assert isinstance(data, dict)
        assert "success" in data
        assert "chunks" in data
        assert "chunk_count" in data
        assert "original_length" in data
        assert "max_length" in data
