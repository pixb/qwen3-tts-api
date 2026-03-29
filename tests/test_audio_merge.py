import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path
import io

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from qwen3_tts_api.main import app


client = TestClient(app)

# 测试音频文件目录
SPLIT_AUDIO_DIR = Path(__file__).parent.parent / "res" / "split"
MERGED_OUTPUT_DIR = SPLIT_AUDIO_DIR


class TestAudioMergeAPI:
    """音频合并API测试"""

    def test_merge_two_audio_files(self):
        """合并两个音频文件测试"""
        audio_1 = SPLIT_AUDIO_DIR / "1.wav"
        audio_2 = SPLIT_AUDIO_DIR / "2.wav"

        assert audio_1.exists(), f"Test audio not found: {audio_1}"
        assert audio_2.exists(), f"Test audio not found: {audio_2}"

        # 使用文件句柄
        files = [
            ("files", (audio_1.name, open(audio_1, "rb"), "audio/wav")),
            ("files", (audio_2.name, open(audio_2, "rb"), "audio/wav")),
        ]
        
        try:
            response = client.post("/audio/merge", files=files)
        finally:
            for item in files:
                item[1][1].close()

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("audio/wav")
        
        # 保存合并后的文件到 res/split 目录
        output_path = MERGED_OUTPUT_DIR / "merged_test_2files.wav"
        with open(output_path, "wb") as f:
            f.write(response.content)
        
        assert output_path.exists()
        print(f"Merged audio saved to: {output_path}")

    def test_merge_four_audio_files(self):
        """合并四个音频文件测试"""
        audio_files = [SPLIT_AUDIO_DIR / f"{i}.wav" for i in range(1, 5)]
        
        for f in audio_files:
            assert f.exists(), f"Test audio not found: {f}"

        files = [
            ("files", (f.name, open(f, "rb"), "audio/wav"))
            for f in audio_files
        ]
        
        try:
            response = client.post("/audio/merge", files=files)
        finally:
            for item in files:
                item[1][1].close()

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("audio/wav")
        
        # 保存合并后的文件到 res/split 目录
        output_path = MERGED_OUTPUT_DIR / "merged_test_4files.wav"
        with open(output_path, "wb") as f:
            f.write(response.content)
        
        assert output_path.exists()
        print(f"Merged audio saved to: {output_path}")

    def test_merge_requires_at_least_two_files(self):
        """至少需要两个文件测试"""
        response = client.post("/audio/merge")
        assert response.status_code == 422

    def test_merge_single_file_fails(self):
        """单个文件合并失败测试"""
        audio_1 = SPLIT_AUDIO_DIR / "1.wav"
        
        files = [
            ("files", (audio_1.name, open(audio_1, "rb"), "audio/wav")),
        ]
        
        try:
            response = client.post("/audio/merge", files=files)
        finally:
            for item in files:
                item[1][1].close()

        assert response.status_code == 400
        assert "At least 2 audio files" in response.json()["detail"]

    def test_merge_different_formats(self):
        """测试相同格式不同文件合并"""
        audio_1 = SPLIT_AUDIO_DIR / "1.wav"
        audio_3 = SPLIT_AUDIO_DIR / "3.wav"

        files = [
            ("files", (audio_1.name, open(audio_1, "rb"), "audio/wav")),
            ("files", (audio_3.name, open(audio_3, "rb"), "audio/wav")),
        ]
        
        try:
            response = client.post("/audio/merge", files=files)
        finally:
            for item in files:
                item[1][1].close()

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("audio/wav")
