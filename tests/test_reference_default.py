import pytest
import requests


BASE_URL = "http://localhost:8001"


class TestReferenceDefault:
    def test_get_default_reference(self):
        """获取默认参考音频"""
        url = f"{BASE_URL}/tts/reference/default"
        
        response = requests.get(url)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_set_default_reference(self):
        """设置默认参考音频"""
        # 先获取列表
        list_url = f"{BASE_URL}/tts/reference/list"
        response = requests.get(list_url)
        data = response.json()
        
        if data["total"] == 0:
            pytest.skip("No reference available")
        
        reference_id = data["data"][0]["id"]
        
        url = f"{BASE_URL}/tts/reference/default/{reference_id}"
        response = requests.post(url)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
