import pytest
import requests


BASE_URL = "http://localhost:8001"


class TestReferenceDetail:
    def test_get_reference_detail(self):
        """获取单个参考音频详情"""
        # 先获取列表
        list_url = f"{BASE_URL}/tts/reference/list"
        response = requests.get(list_url)
        data = response.json()
        
        if data["total"] == 0:
            pytest.skip("No reference available")
        
        reference_id = data["data"][0]["id"]
        
        url = f"{BASE_URL}/tts/reference/{reference_id}"
        response = requests.get(url)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "name" in data["data"]
        assert "file_path" in data["data"]
        print(data)

    def test_get_reference_not_found(self):
        """获取不存在的参考音频"""
        url = f"{BASE_URL}/tts/reference/99999"
        
        response = requests.get(url)
        
        assert response.status_code == 404
        print(response)
