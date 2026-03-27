import pytest
import requests


BASE_URL = "http://localhost:8001"


class TestReferenceAudio:
    def test_download_reference_audio(self):
        """下载参考音频"""
        # 先获取列表
        list_url = f"{BASE_URL}/tts/reference/list"
        response = requests.get(list_url)
        data = response.json()
        
        if data["total"] == 0:
            pytest.skip("No reference available")
        
        reference_id = data["data"][0]["id"]
        
        url = f"{BASE_URL}/tts/reference/{reference_id}/audio"
        print(url)
        response = requests.get(url)
        print(response) 
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("audio/")
