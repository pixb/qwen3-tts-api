import pytest
import requests


BASE_URL = "http://localhost:8001"


class TestReferenceList:
    def test_list_references(self):
        """列出所有参考音频"""
        url = f"{BASE_URL}/tts/reference/list"
        
        response = requests.get(url)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "total" in data
        assert "data" in data
        assert isinstance(data["data"], list)
        print(data)
