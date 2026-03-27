import pytest
import requests
import os


BASE_URL = "http://localhost:8001"


class TestReferenceDelete:
    def test_delete_reference(self):
        """删除参考音频"""
        # 先上传一个
        url = f"{BASE_URL}/tts/reference/upload"
        audio_path = "res/audio/liuyandong.mp3"
        
        if not os.path.exists(audio_path):
            pytest.skip("Sample audio file not found")

        with open(audio_path, "rb") as f:
            response = requests.post(
                url,
                data={"name": "待删除"},
                files={"file": f},
            )
        
        if response.status_code != 200:
            pytest.skip("Failed to upload test reference")
        
        reference_id = response.json()["data"]["id"]
        
        # 删除
        delete_url = f"{BASE_URL}/tts/reference/{reference_id}"
        response = requests.delete(delete_url)
        
        assert response.status_code == 200
        print(response)

    def test_delete_not_found(self):
        """删除不存在的参考音频"""
        url = f"{BASE_URL}/tts/reference/99999"
        
        response = requests.delete(url)
        
        assert response.status_code == 404
        print(response)
