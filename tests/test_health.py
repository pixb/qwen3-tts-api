import pytest
import requests


BASE_URL = "http://localhost:8001"


class TestHealth:
    def test_health_check(self):
        """健康检查接口"""
        url = f"{BASE_URL}/health"
        
        response = requests.get(url)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "device" in data
        assert "model" in data
        assert "supported_languages" in data
        print(data)

    def test_health_returns_json(self):
        """健康检查返回正确的JSON格式"""
        url = f"{BASE_URL}/health"
        
        response = requests.get(url)
        
        assert response.headers["content-type"].startswith("application/json")
        data = response.json()
        assert isinstance(data, dict)
        print(data)
