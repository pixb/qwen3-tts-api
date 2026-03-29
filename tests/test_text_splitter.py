import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from qwen3_tts_api.services.text_splitter import TextSplitter, split_text, SplitResult


class TestTextSplitter:
    def test_split_basic(self):
        """基本拆分测试"""
        text = "这是一个测试文本。我们希望将它拆分成小于200个字符的片段。"
        splitter = TextSplitter(max_length=50)
        result = splitter.split(text)
        
        assert isinstance(result, SplitResult)
        assert len(result.chunks) > 0
        for chunk in result.chunks:
            assert len(chunk) <= 50

    def test_split_chinese(self):
        """中文拆分测试"""
        text = "这是一个测试文本。我们希望将它拆分成小于20个字符的片段。这是一段很长的文字，用于测试当段落超过最大长度时的处理情况。"
        result = split_text(text, max_length=20)
        
        assert result.metadata["original_length"] > 0
        assert result.metadata["chunk_count"] > 1
        for chunk in result.chunks:
            assert len(chunk) <= 20

    def test_split_english(self):
        """英文拆分测试"""
        text = "This is a test text. We want to split it into chunks of less than 50 characters."
        result = split_text(text, max_length=30)
        
        assert result.metadata["chunk_count"] > 0
        for chunk in result.chunks:
            assert len(chunk) <= 30

    def test_split_empty(self):
        """空文本测试"""
        result = split_text("")
        
        assert result.chunks == []
        assert result.metadata["original_length"] == 0

    def test_split_multiple_paragraphs(self):
        """多段落拆分测试"""
        text = """这是第一段内容。我们在这里测试多段落的拆分功能。

这是第二段内容。它包含更多的内容，用于测试拆分功能。

这里是第三段。我们继续添加更多的内容，以确保测试的准确性。这是一段很长的文字，用于测试当段落超过最大长度时的处理情况。"""
        
        result = split_text(text, max_length=50)
        
        assert result.metadata["chunk_count"] > 0
        for chunk in result.chunks:
            assert len(chunk) <= 50

    def test_split_no_merge(self):
        """不合并短片段测试"""
        text = "这是第一句。这是第二句。这是一句很短的句子。"
        result = split_text(text, max_length=50, merge_short=False)
        
        assert len(result.chunks) > 0

    def test_split_custom_min_length(self):
        """自定义最小片段长度测试"""
        text = "短。句子。测试。"
        result = split_text(text, max_length=50, min_chunk_length=10, merge_short=True)
        
        assert result.metadata["chunk_count"] > 0

    def test_split_metadata(self):
        """元数据测试"""
        text = "这是一个测试文本。我们希望将它拆分成小于30个字符的片段。这是一段很长的文字，用于测试当段落超过最大长度时的处理情况。"
        result = split_text(text, max_length=30)
        
        assert "original_length" in result.metadata
        assert "chunk_count" in result.metadata
        assert "max_length" in result.metadata
        assert result.metadata["original_length"] > 0
        assert result.metadata["chunk_count"] > 0

    def test_split_long_sentence(self):
        """超长句子拆分测试"""
        text = "这是一段非常非常长的文字，用于测试当单个句子就超过最大长度时的处理情况。我们需要在适当的位置进行拆分，同时保持语义的完整性。"
        result = split_text(text, max_length=30)
        
        assert result.metadata["chunk_count"] > 1
        for chunk in result.chunks:
            assert len(chunk) <= 30

    def test_split_mixed_language(self):
        """中英混合拆分测试"""
        text = "你好，这是一个测试。Hello, this is a test. 我们来测试混合语言的拆分。"
        result = split_text(text, max_length=30)
        
        assert result.metadata["chunk_count"] > 0
