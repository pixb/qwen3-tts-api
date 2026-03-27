import pytest
import requests
import os


BASE_URL = "http://localhost:8001"


class TestReferenceUpload:
    def test_upload_reference_basic(self):
        """上传参考音频"""
        url = f"{BASE_URL}/tts/reference/upload"
        
        audio_path = "res/audio/liuyandong.mp3"
        if not os.path.exists(audio_path):
            audio_path = "res/audio/tianyuan.mp3"
        
        if not os.path.exists(audio_path):
            pytest.skip("Sample audio file not found")

        with open(audio_path, "rb") as f:
            response = requests.post(
                url,
                data={
                    "name": "测试参考音频",
                    "ref_text": "这是参考文本",
                    "language": "Chinese",
                    "exaggeration": 0.5,
                    "temperature": 0.8,
                    "speed_rate": 1.0,
                },
                files={"file": f},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "id" in data["data"]
        print(data)

    def test_upload_reference_minimal(self):
        """最简上传（仅必需参数）"""
        url = f"{BASE_URL}/tts/reference/upload"
        
        audio_path = "res/audio/tianyuan.mp3"
        if not os.path.exists(audio_path):
            pytest.skip("Sample audio file not found")

        with open(audio_path, "rb") as f:
            response = requests.post(
                url,
                data={"name": "最简上传测试"},
                files={"file": f},
            )

        assert response.status_code == 200
        print(response)

    def test_upload_reference_with_default(self):
        """上传并设为默认"""
        url = f"{BASE_URL}/tts/reference/upload"
        
        audio_path = "res/audio/liuyandong.mp3"
        if not os.path.exists(audio_path):
            pytest.skip("Sample audio file not found")

        with open(audio_path, "rb") as f:
            response = requests.post(
                url,
                data={
                    "name": "默认测试参考音频",
                    "is_default": 1,
                },
                files={"file": f},
            )
            print(response)

        assert response.status_code == 200
