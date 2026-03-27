import pytest
import requests


BASE_URL = "http://localhost:8001"


class TestReferenceUpdate:
    def test_update_reference_name(self):
        """更新参考音频名称"""
        # 先获取列表
        list_url = f"{BASE_URL}/tts/reference/list"
        response = requests.get(list_url)
        data = response.json()
        
        if data["total"] == 0:
            pytest.skip("No reference available")
        
        reference_id = data["data"][0]["id"]
        
        url = f"{BASE_URL}/tts/reference/{reference_id}"
        response = requests.post(
            url,
            data={"name": "新名称"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        print(data)

    def test_update_reference_params(self):
        """更新参考音频参数"""
        # 先获取列表
        list_url = f"{BASE_URL}/tts/reference/list"
        response = requests.get(list_url)
        data = response.json()
        
        if data["total"] == 0:
            pytest.skip("No reference available")
        
        reference_id = data["data"][0]["id"]
        
        url = f"{BASE_URL}/tts/reference/{reference_id}"
        response = requests.post(
            url,
            data={
                "exaggeration": 0.7,
                "temperature": 0.9,
                "speed_rate": 1.2,
            },
        )
        
        assert response.status_code == 200
        print(response.json())
