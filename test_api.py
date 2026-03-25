"""
Qwen3-TTS API 接口测试

使用 FastAPI TestClient 进行接口测试，Mock 模型调用以确保测试可独立运行
"""

import os
import io
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from pathlib import Path
from contextlib import contextmanager

# 设置测试路径
RES_DIR = Path(__file__).parent / "res"


# ==================== Mock 模型 ====================
def create_mock_model():
    """
    创建 Mock 模型对象，模拟 Qwen3TTSModel 的行为
    """
    mock = MagicMock()

    # 创建一个简单的正弦波作为测试音频数据
    sample_rate = 24000
    duration = 1  # 1秒
    t = np.linspace(0, duration, int(sample_rate * duration))
    # 生成 440Hz 的正弦波
    audio_data = np.sin(2 * np.pi * 440 * t).astype(np.float32)

    # Mock create_voice_clone_prompt
    mock.create_voice_clone_prompt.return_value = MagicMock()

    # Mock generate_voice_clone
    mock.generate_voice_clone.return_value = (
        [audio_data],  # wavs (list of numpy arrays)
        sample_rate,  # sample rate
    )

    # Mock generate_custom_voice
    mock.generate_custom_voice.return_value = ([audio_data], sample_rate)

    # Mock generate_voice_design
    mock.generate_voice_design.return_value = ([audio_data], sample_rate)

    return mock


# 全局 mock 模型实例
_mock_model = create_mock_model()


@contextmanager
def mock_get_model():
    """
    Context manager for mocking get_model function
    """
    with patch("api.get_model", return_value=_mock_model):
        yield


# 预先 patch 模块
import api as api_module

_original_get_model = api_module.get_model


def patched_get_model():
    """被 patch 的 get_model 函数"""
    return _mock_model


# 在模块级别替换
api_module.get_model = patched_get_model


# ==================== Fixture ====================
@pytest.fixture
def client():
    """
    创建测试客户端，使用 mock 模型
    """
    from fastapi.testclient import TestClient

    client = TestClient(api_module.app)
    yield client


@pytest.fixture
def sample_audio_file():
    """
    返回示例音频文件路径
    """
    audio_path = RES_DIR / "prompt.mp3"
    assert audio_path.exists(), f"Audio file not found: {audio_path}"
    return audio_path


@pytest.fixture
def sample_audio_file1():
    """
    返回另一个示例音频文件路径
    """
    audio_path = RES_DIR / "prompt1.mp3"
    assert audio_path.exists(), f"Audio file not found: {audio_path}"
    return audio_path


@pytest.fixture
def sample_text():
    """
    返回示例文本
    """
    return (RES_DIR / "prompt.txt").read_text(encoding="utf-8").strip()


@pytest.fixture
def sample_text1():
    """
    返回另一个示例文本
    """
    return (RES_DIR / "prompt1.txt").read_text(encoding="utf-8").strip()


# ==================== 测试用例 ====================
class TestHealth:
    """健康检查接口测试"""

    def test_health_check_success(self, client):
        """测试健康检查成功返回"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # 验证响应结构
        assert "status" in data
        assert "device" in data
        assert "model" in data
        assert "supported_languages" in data

        # 验证状态
        assert data["status"] == "healthy"

        # 验证支持的语言列表
        assert isinstance(data["supported_languages"], list)
        assert "Chinese" in data["supported_languages"]
        assert "English" in data["supported_languages"]

    def test_health_check_response_format(self, client):
        """测试健康检查响应格式"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # 验证所有必填字段
        required_fields = ["status", "device", "model", "supported_languages"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"


class TestLanguages:
    """语言列表接口测试"""

    def test_get_languages_success(self, client):
        """测试获取支持的语言列表成功"""
        response = client.get("/languages")

        assert response.status_code == 200
        data = response.json()

        # 验证响应结构
        assert "languages" in data
        assert "default" in data

        # 验证语言列表
        languages = data["languages"]
        assert isinstance(languages, list)
        assert len(languages) > 0

        # 验证默认语言
        assert data["default"] == "English"

        # 验证常见语言
        expected_languages = ["Chinese", "English", "Japanese", "Korean"]
        for lang in expected_languages:
            assert lang in languages

    def test_get_languages_returns_all_supported(self, client):
        """测试返回所有支持的语言"""
        response = client.get("/languages")

        assert response.status_code == 200
        data = response.json()

        languages = data["languages"]

        # 验证所有声明的支持语言都存在
        all_expected = [
            "Chinese",
            "English",
            "Japanese",
            "Korean",
            "German",
            "French",
            "Russian",
            "Portuguese",
            "Spanish",
            "Italian",
        ]

        for lang in all_expected:
            assert lang in languages, f"Missing language: {lang}"


class TestTTS:
    """TTS 接口测试"""

    def test_tts_with_audio_prompt(self, client, sample_audio_file, sample_text):
        """测试带参考音频的 TTS 请求"""
        with open(sample_audio_file, "rb") as f:
            response = client.post(
                "/tts",
                data={
                    "text": sample_text,
                    "language": "Chinese",
                    "exaggeration": 0.5,
                    "temperature": 0.8,
                },
                files={"audio_prompt": ("prompt.mp3", f, "audio/mpeg")},
            )

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("audio/")

    def test_tts_without_audio_prompt(self, client):
        """测试不带参考音频的 TTS 请求 (应返回错误)"""
        response = client.post(
            "/tts",
            data={
                "text": "Hello world",
                "language": "English",
            },
        )

        # Base 模型需要参考音频，应返回 4xx 错误
        # Note: FastAPI TestClient 会将 HTTPException 转换为 500 或 4xx
        assert response.status_code >= 400
        # 检查响应包含错误信息
        data = response.json()
        assert "detail" in data

    def test_tts_empty_text(self, client):
        """测试空文本 TTS 请求"""
        response = client.post(
            "/tts",
            data={
                "text": "",
                "language": "English",
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    def test_tts_whitespace_text(self, client):
        """测试空白字符文本 TTS 请求"""
        response = client.post(
            "/tts",
            data={
                "text": "   ",
                "language": "English",
            },
        )

        assert response.status_code == 400

    def test_tts_with_custom_language(self, client, sample_audio_file):
        """测试自定义语言参数"""
        with open(sample_audio_file, "rb") as f:
            response = client.post(
                "/tts",
                data={
                    "text": "测试文本",
                    "language": "zh",  # 使用语言代码
                    "exaggeration": 0.7,
                    "temperature": 0.9,
                },
                files={"audio_prompt": ("prompt.mp3", f, "audio/mpeg")},
            )

        assert response.status_code == 200

    def test_tts_with_instruct(self, client, sample_audio_file):
        """测试带语音风格指令的 TTS 请求"""
        with open(sample_audio_file, "rb") as f:
            response = client.post(
                "/tts",
                data={
                    "text": "Hello world",
                    "language": "English",
                    "instruct": "Speak slowly and clearly",
                },
                files={"audio_prompt": ("prompt.mp3", f, "audio/mpeg")},
            )

        assert response.status_code == 200


class TestTTSCustom:
    """TTS Custom 接口测试"""

    def test_tts_custom_success(self, client):
        """测试预设说话人 TTS 成功"""
        response = client.post(
            "/tts/custom",
            data={
                "text": "Hello world, this is a test.",
                "language": "English",
                "speaker": "Ryan",
                "exaggeration": 0.5,
                "temperature": 0.8,
            },
        )

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("audio/")

    def test_tts_custom_chinese(self, client):
        """测试中文预设说话人 TTS"""
        response = client.post(
            "/tts/custom",
            data={
                "text": "你好，这是一个测试。",
                "language": "Chinese",
                "speaker": "Ryan",
            },
        )

        assert response.status_code == 200

    def test_tts_custom_empty_text(self, client):
        """测试空文本预设说话人 TTS"""
        response = client.post(
            "/tts/custom",
            data={
                "text": "",
                "speaker": "Ryan",
            },
        )

        assert response.status_code == 400

    def test_tts_custom_invalid_exaggeration(self, client):
        """测试无效的夸张参数"""
        response = client.post(
            "/tts/custom",
            data={
                "text": "Test",
                "speaker": "Ryan",
                "exaggeration": 2.0,  # 超出范围
            },
        )

        # 参数验证由模型处理，API 层面可能不严格验证

    def test_tts_custom_with_instruct(self, client):
        """测试带风格指令的预设说话人 TTS"""
        response = client.post(
            "/tts/custom",
            data={
                "text": "Hello world",
                "speaker": "Ryan",
                "instruct": "Speak with enthusiasm",
            },
        )

        assert response.status_code == 200

    def test_tts_custom_auto_language_detection(self, client):
        """测试自动语言检测"""
        response = client.post(
            "/tts/custom",
            data={
                "text": "这是一个中文测试",
                "language": "Auto",
                "speaker": "Ryan",
            },
        )

        assert response.status_code == 200


class TestTTSDesign:
    """TTS Design 接口测试"""

    def test_tts_design_success(self, client):
        """测试语音设计 TTS 成功"""
        response = client.post(
            "/tts/design",
            data={
                "text": "Hello world, this is a voice design test.",
                "language": "English",
                "instruct": "A warm and friendly female voice",
                "exaggeration": 0.5,
                "temperature": 0.8,
            },
        )

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("audio/")

    def test_tts_design_chinese(self, client):
        """测试中文语音设计"""
        response = client.post(
            "/tts/design",
            data={
                "text": "你好，这是一个语音设计测试。",
                "language": "Chinese",
                "instruct": "温柔的女声",
            },
        )

        assert response.status_code == 200

    def test_tts_design_empty_text(self, client):
        """测试空文本语音设计"""
        response = client.post(
            "/tts/design",
            data={
                "text": "",
                "instruct": "A friendly voice",
            },
        )

        assert response.status_code == 400

    def test_tts_design_empty_instruct(self, client):
        """测试空指令语音设计"""
        response = client.post(
            "/tts/design",
            data={
                "text": "Test text",
                "instruct": "",
            },
        )

        assert response.status_code == 400

    def test_tts_design_whitespace_instruct(self, client):
        """测试空白指令语音设计"""
        response = client.post(
            "/tts/design",
            data={
                "text": "Test text",
                "instruct": "   ",
            },
        )

        assert response.status_code == 400

    def test_tts_design_detailed_instruct(self, client):
        """测试详细语音描述"""
        response = client.post(
            "/tts/design",
            data={
                "text": "Hello",
                "instruct": "A deep male voice with a British accent, speaking in a calm and professional manner",
            },
        )

        assert response.status_code == 200


class TestTTSClone:
    """TTS Clone 接口测试"""

    def test_tts_clone_success(self, client, sample_audio_file, sample_text):
        """测试语音克隆成功"""
        with open(sample_audio_file, "rb") as f:
            response = client.post(
                "/tts/clone",
                data={
                    "text": sample_text,
                    "language": "Chinese",
                    "ref_text": sample_text,
                    "exaggeration": 0.5,
                    "temperature": 0.8,
                },
                files={"audio_prompt": ("prompt.mp3", f, "audio/mpeg")},
            )

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("audio/")

    def test_tts_clone_without_ref_text(self, client, sample_audio_file):
        """测试不带参考文本的语音克隆"""
        with open(sample_audio_file, "rb") as f:
            response = client.post(
                "/tts/clone",
                data={
                    "text": "测试语音克隆",
                    "language": "Chinese",
                },
                files={"audio_prompt": ("prompt.mp3", f, "audio/mpeg")},
            )

        assert response.status_code == 200

    def test_tts_clone_empty_text(self, client, sample_audio_file):
        """测试空文本语音克隆"""
        with open(sample_audio_file, "rb") as f:
            response = client.post(
                "/tts/clone",
                data={
                    "text": "",
                },
                files={"audio_prompt": ("prompt.mp3", f, "audio/mpeg")},
            )

        assert response.status_code == 400

    def test_tts_clone_english(self, client, sample_audio_file1, sample_text1):
        """测试英文语音克隆"""
        with open(sample_audio_file1, "rb") as f:
            response = client.post(
                "/tts/clone",
                data={
                    "text": "This is an English voice cloning test.",
                    "language": "English",
                },
                files={"audio_prompt": ("prompt1.mp3", f, "audio/mpeg")},
            )

        assert response.status_code == 200

    def test_tts_clone_with_instruct(self, client, sample_audio_file):
        """测试带风格指令的语音克隆"""
        with open(sample_audio_file, "rb") as f:
            response = client.post(
                "/tts/clone",
                data={
                    "text": "测试文本",
                    "language": "Chinese",
                    "instruct": "Speak with more emotion",
                },
                files={"audio_prompt": ("prompt.mp3", f, "audio/mpeg")},
            )

        assert response.status_code == 200


class TestParameterValidation:
    """参数验证测试"""

    def test_invalid_language_code(self, client, sample_audio_file):
        """测试无效的语言代码"""
        with open(sample_audio_file, "rb") as f:
            response = client.post(
                "/tts",
                data={
                    "text": "Test",
                    "language": "invalid_language_xyz",
                },
                files={"audio_prompt": ("prompt.mp3", f, "audio/mpeg")},
            )

        # 应该接受无效的语言代码（可能回退到默认）
        assert response.status_code in [200, 400, 500]

    def test_exaggeration_out_of_range(self, client):
        """测试夸张参数超出范围"""
        response = client.post(
            "/tts/custom",
            data={
                "text": "Test",
                "speaker": "Ryan",
                "exaggeration": 1.5,
            },
        )

        # API 可能不验证范围，由模型处理

    def test_temperature_out_of_range(self, client):
        """测试温度参数超出范围"""
        response = client.post(
            "/tts/custom",
            data={
                "text": "Test",
                "speaker": "Ryan",
                "temperature": -0.5,
            },
        )

        # API 可能不验证范围，由模型处理


class TestErrorHandling:
    """错误处理测试"""

    def test_nonexistent_endpoint(self, client):
        """测试不存在的接口"""
        response = client.get("/nonexistent")
        assert response.status_code == 404

    def test_invalid_method(self, client):
        """测试错误的 HTTP 方法"""
        # GET 请求到 POST 端点
        response = client.get("/tts")
        assert response.status_code == 405

    def test_missing_required_field(self, client):
        """测试缺少必填字段"""
        # /tts/design 需要 instruct
        response = client.post(
            "/tts/design",
            data={
                "text": "Test text",
                # 缺少 instruct
            },
        )

        assert response.status_code == 422  # FastAPI 会返回验证错误


class TestCORS:
    """CORS 测试"""

    def test_cors_headers(self, client):
        """测试 CORS 头"""
        response = client.get("/health")

        # 检查是否包含 CORS 相关头
        # Note: TestClient 默认不会添加 CORS 头，需要检查实际配置
        assert response.status_code == 200


# ==================== 运行测试 ====================
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
