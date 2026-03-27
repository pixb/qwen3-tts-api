import pytest
import requests


BASE_URL = "http://localhost:8001"


class TestLanguages:
    def test_get_languages(self):
        """获取支持的语言列表"""
        url = f"{BASE_URL}/languages"
        
        response = requests.get(url)
        
        assert response.status_code == 200
        data = response.json()
        assert "languages" in data
        assert "default" in data
        assert isinstance(data["languages"], list)
        assert len(data["languages"]) > 0
        print(data)

    def test_languages_contains_common(self):
        """语言列表包含常见语言"""
        url = f"{BASE_URL}/languages"
        
        response = requests.get(url)
        
        data = response.json()
        common_langs = ["Chinese", "English", "Japanese", "Korean"]
        for lang in common_langs:
            assert any(lang.lower() in l.lower() for l in data["languages"])
        print(data)

    def test_languages_returns_json(self):
        """语言接口返回正确的JSON格式"""
        url = f"{BASE_URL}/languages"
        
        response = requests.get(url)
        
        assert response.headers["content-type"].startswith("application/json")
        data = response.json()
        assert isinstance(data, dict)
        print(data)
