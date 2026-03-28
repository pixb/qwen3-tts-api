import os
import pytest
import requests
import time


BASE_URL = "http://localhost:8001"


class TestReference:
    reference_id = None

    @classmethod
    def setup_class(cls):
        """确保有一个可用的参考音频"""
        url = f"{BASE_URL}/tts/reference/list"
        response = requests.get(url)
        data = response.json()

        if data["total"] > 0:
            cls.reference_id = data["data"][0]["id"]
            return

        audio_path = "res/audio/liuyandong.mp3"
        if not os.path.exists(audio_path):
            audio_path = "res/audio/tianyuan.mp3"

        if not os.path.exists(audio_path):
            pytest.skip("Sample audio file not found")

        upload_url = f"{BASE_URL}/tts/reference/upload"
        with open(audio_path, "rb") as f:
            response = requests.post(
                upload_url,
                data={"name": "测试参考音频-setup"},
                files={"file": f},
            )

        if response.status_code == 200:
            cls.reference_id = response.json()["data"]["id"]

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
                    "name": "测试参考音频-{}".format(time.time()),
                    "ref_text": "这是参考文本",
                    "language": "Chinese",
                    "exaggeration": 0.5,
                    "temperature": 0.8,
                    "speed_rate": 1.0,
                },
                files={"file": f},
            )
        print(response.json())
        assert response.status_code == 200
        data = response.json()
        print(data)
        assert data["success"] is True
        assert "id" in data["data"]

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

    def test_get_default_reference(self):
        """获取默认参考音频"""
        url = f"{BASE_URL}/tts/reference/default"
        
        response = requests.get(url)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_set_default_reference(self):
        """设置默认参考音频"""
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

    def test_get_reference_detail(self):
        """获取单个参考音频详情"""
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

    def test_download_reference_audio(self):
        """下载参考音频"""
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

    def test_update_reference_name(self):
        """更新参考音频名称"""
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

    def test_delete_reference(self):
        """删除参考音频"""
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
