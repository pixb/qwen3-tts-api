import pytest
import requests


BASE_URL = "http://localhost:8001"


class TestTTSGenerate:
    def test_generate_with_reference_id(self):
        """使用参考音频ID生成"""
        # 先获取参考音频列表
        list_url = f"{BASE_URL}/tts/reference/list"
        response = requests.get(list_url)
        data = response.json()
        
        if data["total"] == 0:
            pytest.skip("No reference available")
        
        reference_id = data["data"][0]["id"]
        
        url = f"{BASE_URL}/tts/generate"
        response = requests.post(
            url,
            data={
                "text": "你好，这是一段测试",
                "reference_id": reference_id,
                "ref_text": "这是参考文本",
            },
        )

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("audio/")

    def test_generate_with_reference_name(self):
        """使用参考音频名称生成"""
        # 先获取参考音频列表
        list_url = f"{BASE_URL}/tts/reference/list"
        response = requests.get(list_url)
        data = response.json()
        
        if data["total"] == 0:
            pytest.skip("No reference available")
        
        reference_name = data["data"][0]["name"]
        
        url = f"{BASE_URL}/tts/generate"
        response = requests.post(
            url,
            data={
                "text": "Hello world",
                "reference_name": reference_name,
                "ref_text": "这是参考文本",
            },
        )

        assert response.status_code == 200

    def test_generate_with_custom_params(self):
        """使用自定义参数覆盖默认值"""
        # 先获取参考音频列表
        list_url = f"{BASE_URL}/tts/reference/list"
        response = requests.get(list_url)
        data = response.json()
        
        if data["total"] == 0:
            pytest.skip("No reference available")
        
        reference_id = data["data"][0]["id"]
        
        url = f"{BASE_URL}/tts/generate"
        response = requests.post(
            url,
            data={
                "text": "测试自定义参数",
                "reference_id": reference_id,
                "ref_text": "这是参考文本",
                "exaggeration": 0.7,
                "temperature": 0.9,
                "speed_rate": 1.2,
            },
        )

        assert response.status_code == 200

    def test_generate_missing_reference(self):
        """缺少参考音频应返回错误"""
        url = f"{BASE_URL}/tts/generate"
        response = requests.post(
            url,
            data={
                "text": "测试文字",
                "ref_text": "这是参考文本",
            },
        )

        assert response.status_code == 400

    def test_generate_invalid_reference_id(self):
        """无效的参考音频ID"""
        url = f"{BASE_URL}/tts/generate"
        response = requests.post(
            url,
            data={
                "text": "测试文字",
                "ref_text": "这是参考文本",
                "reference_id": 99999,
            },
        )

        assert response.status_code == 404

    def test_generate_invalid_reference_name(self):
        """无效的参考音频名称"""
        url = f"{BASE_URL}/tts/generate"
        response = requests.post(
            url,
            data={
                "text": "测试文字",
                "ref_text": "这是参考文本",
                "reference_name": "不存在的名称",
            },
        )

        assert response.status_code == 404

    def test_generate_english(self):
        """英语文本生成"""
        # 先获取参考音频列表
        list_url = f"{BASE_URL}/tts/reference/list"
        response = requests.get(list_url)
        data = response.json()
        
        if data["total"] == 0:
            pytest.skip("No reference available")
        
        reference_id = data["data"][0]["id"]
        
        url = f"{BASE_URL}/tts/generate"
        response = requests.post(
            url,
            data={
                "text": "Hello world, this is a test",
                "reference_id": reference_id,
                "ref_text": "这是参考文本",
                "language": "English",
            },
        )

        assert response.status_code == 200

    def test_generate_empty_text(self):
        """空文本应返回错误"""
        # 先获取参考音频列表
        list_url = f"{BASE_URL}/tts/reference/list"
        response = requests.get(list_url)
        data = response.json()
        
        if data["total"] == 0:
            pytest.skip("No reference available")
        
        reference_id = data["data"][0]["id"]
        
        url = f"{BASE_URL}/tts/generate"
        response = requests.post(
            url,
            data={
                "text": "",
                "reference_id": reference_id,
                "ref_text": "这是参考文本",
            },
        )

        assert response.status_code == 400
