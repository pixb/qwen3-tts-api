import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path
import io

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from qwen3_tts_api.main import app


client = TestClient(app)

TEST_AUDIO_DIR = Path(__file__).parent.parent / "res"
OUTPUT_DIR = Path(__file__).parent.parent / "output"


class TestAudioUploadAPI:
    """音频上传API测试"""

    def test_upload_audio(self):
        """上传音频文件测试"""
        audio_file = TEST_AUDIO_DIR / "liuyandong.mp3"
        assert audio_file.exists(), f"Test audio not found: {audio_file}"

        with open(audio_file, "rb") as f:
            response = client.post(
                "/audio/upload",
                files={"file": (audio_file.name, f, "audio/mp3")}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "filename" in data
        assert "url" in data
        assert data["url"].startswith("/audio/")
        assert "size" in data
        assert data["size"] > 0

        print(f"Uploaded: {data['filename']}, URL: {data['url']}, Size: {data['size']}")

    def test_upload_wav_audio(self):
        """上传WAV音频文件测试"""
        audio_file = TEST_AUDIO_DIR / "liuyandong2.wav"
        assert audio_file.exists(), f"Test audio not found: {audio_file}"

        with open(audio_file, "rb") as f:
            response = client.post(
                "/audio/upload",
                files={"file": (audio_file.name, f, "audio/wav")}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "filename" in data
        assert ".wav" in data["filename"]

    def test_upload_unsupported_format(self):
        """上传不支持的格式测试"""
        response = client.post(
            "/audio/upload",
            files={"file": ("test.txt", io.BytesIO(b"not an audio file"), "text/plain")}
        )

        assert response.status_code == 400
        assert "Unsupported audio format" in response.json()["detail"]


class TestAudioDownloadAPI:
    """音频下载API测试"""

    def test_download_uploaded_audio(self):
        """下载已上传的音频测试"""
        audio_file = TEST_AUDIO_DIR / "liuyandong.mp3"
        assert audio_file.exists(), f"Test audio not found: {audio_file}"

        upload_response = client.post(
            "/audio/upload",
            files={"file": (audio_file.name, open(audio_file, "rb"), "audio/mp3")}
        )
        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        filename = upload_data["filename"]

        download_response = client.get(f"/audio/{filename}")
        assert download_response.status_code == 200
        assert download_response.headers["content-type"].startswith("audio/")

    def test_download_nonexistent_file(self):
        """下载不存在的文件测试"""
        response = client.get("/audio/nonexistent_file.wav")
        assert response.status_code == 404

    def test_audio_url_accessible(self):
        """测试上传后返回的URL可直接访问"""
        audio_file = TEST_AUDIO_DIR / "liuyandong2_clean.wav"
        assert audio_file.exists(), f"Test audio not found: {audio_file}"

        upload_response = client.post(
            "/audio/upload",
            files={"file": (audio_file.name, open(audio_file, "rb"), "audio/wav")}
        )
        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        url = upload_data["url"]

        full_url = f"http://testserver{url}"
        download_response = client.get(url)
        assert download_response.status_code == 200
        assert download_response.headers["content-type"].startswith("audio/")


class TestAudioUploadWorkflow:
    """音频上传下载完整流程测试"""

    def test_upload_merge_download_workflow(self):
        """上传-合并-下载完整流程测试"""
        audio_files = [
            TEST_AUDIO_DIR / "liuyandong.mp3",
            TEST_AUDIO_DIR / "liuyandong2_clean.wav",
        ]

        for f in audio_files:
            assert f.exists(), f"Test audio not found: {f}"

        uploaded_files = []
        for audio_file in audio_files:
            with open(audio_file, "rb") as f:
                response = client.post(
                    "/audio/upload",
                    files={"file": (audio_file.name, f, "audio/mpeg" if audio_file.suffix == ".mp3" else "audio/wav")}
                )
            assert response.status_code == 200
            uploaded_files.append(response.json()["filename"])
            print(f"Uploaded: {response.json()['filename']}")

        print(f"Uploaded files: {uploaded_files}")

        for filename in uploaded_files:
            response = client.get(f"/audio/{filename}")
            assert response.status_code == 200, f"Failed to download {filename}"
            assert response.headers["content-type"].startswith("audio/")

    def test_upload_and_download_merged_audio(self):
        """上传并下载合并后的音频测试"""
        audio_files = [
            TEST_AUDIO_DIR / "liuyandong.mp3",
            TEST_AUDIO_DIR / "liuyandong2_clean.wav",
        ]

        files = [
            ("files", (f.name, open(f, "rb"), "audio/mpeg" if f.suffix == ".mp3" else "audio/wav"))
            for f in audio_files
        ]

        try:
            merge_response = client.post("/audio/merge", files=files)
        finally:
            for item in files:
                item[1][1].close()

        assert merge_response.status_code == 200

        upload_response = client.post(
            "/audio/upload",
            files={"file": ("merged.wav", merge_response.content, "audio/wav")}
        )
        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        assert upload_data["success"] is True

        filename = upload_data["filename"]
        download_response = client.get(f"/audio/{filename}")
        assert download_response.status_code == 200
        assert download_response.headers["content-type"].startswith("audio/")

        print(f"Merged and uploaded: {filename}, URL: {upload_data['url']}")
