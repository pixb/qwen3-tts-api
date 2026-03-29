import pytest
import requests
import os


BASE_URL = "http://localhost:8001"


class TestTTSClone:
    def test_clone_basic(self):
        """基础语音克隆测试"""
        url = f"{BASE_URL}/tts/clone"
        
        # 准备参考音频文件路径
        audio_prompt_path = "res/liuyandong.mp3"
        
        if not os.path.exists(audio_prompt_path):
            pytest.skip("Reference audio file not found")

        with open(audio_prompt_path, "rb") as f:
            response = requests.post(
                url,
                data={
                    "text": "你好，这是一段测试语音",
                    "language": "auto",
                    "ref_text": "这是参考文本",
                    "exaggeration": 0.5,
                    "temperature": 0.8,
                },
                files={"audio_prompt": f},
            )

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("audio/")
        
        # 保存输出文件用于验证
        with open("test_clone_output.wav", "wb") as f:
            f.write(response.content)

    def test_clone_with_ref_text(self):
        """带参考文本的语音克隆"""
        url = f"{BASE_URL}/tts/clone"
        
        audio_prompt_path = "res/liuyandong.mp3"
        
        if not os.path.exists(audio_prompt_path):
            pytest.skip("Reference audio file not found")

        with open(audio_prompt_path, "rb") as f:
            response = requests.post(
                url,
                data={
                    "text": "Hello world",
                    "language": "Chinese",
                    "ref_text": "当时我就觉得这太搞笑了，就这一个动作我反反的复复玩了一下午，每次玩的时候都会笑，在说任天堂故事的时候，我会提起当任天堂发展的时候",
                    "exaggeration": 0.6,
                    "temperature": 0.7,
                },
                files={"audio_prompt": f},
            )

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("audio/")

    def test_clone_missing_audio(self):
        """缺少参考音频应该返回错误"""
        url = f"{BASE_URL}/tts/clone"
        
        response = requests.post(
            url,
            data={
                "text": "测试文字",
                "ref_text": "这是参考文本",
            },
        )

        assert response.status_code == 422  # FastAPI validation error

    def test_clone_empty_text(self):
        """空文本应该返回错误"""
        url = f"{BASE_URL}/tts/clone"
        
        audio_prompt_path = "res/liuyandong.mp3"
        
        if not os.path.exists(audio_prompt_path):
            pytest.skip("Reference audio file not found")

        with open(audio_prompt_path, "rb") as f:
            response = requests.post(
                url,
                data={
                    "text": "",
                    "ref_text": "这是参考文本",
                },
                files={"audio_prompt": f},
            )

        assert response.status_code == 422

    def test_clone_with_speed_rate(self):
        """测试语速调整"""
        url = f"{BASE_URL}/tts/clone"
        
        audio_prompt_path = "res/liuyandong.mp3"
        
        if not os.path.exists(audio_prompt_path):
            pytest.skip("Reference audio file not found")

        with open(audio_prompt_path, "rb") as f:
            response = requests.post(
                url,
                data={
                    "text": "测试语速调整",
                    "ref_text": "这是参考文本",
                    "speed_rate": 1.5,
                },
                files={"audio_prompt": f},
            )

        assert response.status_code == 200
