"""文本拆分核心模块"""

import re
from dataclasses import dataclass
from typing import List


@dataclass
class SplitResult:
    """拆分结果"""
    chunks: List[str]
    metadata: dict

    def __str__(self) -> str:
        return f"SplitResult(chunk_count={len(self.chunks)}, metadata={self.metadata})"


class TextSplitter:
    """文本拆分器
    
    将长文本按语义拆分为指定大小的片段，支持中文。
    
    拆分策略：
    1. 首先按段落拆分
    2. 对于超出大小的段落，按句子拆分
    3. 对于仍然超出大小的句子，尝试按子句拆分
    4. 合并过短的片段
    """
    
    def __init__(
        self,
        max_length: int = 200,
        min_chunk_length: int = 50,
        merge_short: bool = True,
    ):
        """
        初始化拆分器
        
        Args:
            max_length: 单个片段的最大字符数
            min_chunk_length: 合并短片段的最小长度阈值
            merge_short: 是否合并过短的片段
        """
        self.max_length = max_length
        self.min_chunk_length = min_chunk_length
        self.merge_short = merge_short
        
        self.sentence_endings = r'[。！？\.!?；;]'
        self.paragraph_markers = r'\n\s*\n'
    
    def split(self, text: str) -> SplitResult:
        """拆分文本"""
        if not text or not text.strip():
            return SplitResult(chunks=[], metadata={"original_length": 0})
        
        text = self._clean_text(text)
        
        paragraphs = self._split_paragraphs(text)
        
        chunks = []
        for para in paragraphs:
            para_chunks = self._split_paragraph(para)
            chunks.extend(para_chunks)
        
        if self.merge_short:
            chunks = self._merge_short_chunks(chunks)
        
        metadata = {
            "original_length": len(text),
            "chunk_count": len(chunks),
            "max_length": self.max_length,
        }
        
        return SplitResult(chunks=chunks, metadata=metadata)
    
    def _clean_text(self, text: str) -> str:
        """清理文本"""
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        return text.strip()
    
    def _split_paragraphs(self, text: str) -> List[str]:
        """按段落拆分"""
        paragraphs = re.split(self.paragraph_markers, text)
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _split_paragraph(self, paragraph: str) -> List[str]:
        """拆分单个段落"""
        if len(paragraph) <= self.max_length:
            return [paragraph]
        
        sentences = self._split_sentences(paragraph)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(sentence) > self.max_length:
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = ""
                
                sub_chunks = self._split_long_sentence(sentence)
                chunks.extend(sub_chunks)
                continue
            
            if len(current_chunk) + len(sentence) + 1 <= self.max_length:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _split_sentences(self, text: str) -> List[str]:
        """按句子拆分"""
        pattern = f'({self.sentence_endings})'
        parts = re.split(pattern, text)
        
        sentences = []
        for i in range(0, len(parts) - 1, 2):
            sentence = parts[i]
            if i + 1 < len(parts):
                sentence += parts[i + 1]
            if sentence.strip():
                sentences.append(sentence)
        
        if parts[-1].strip():
            if sentences:
                sentences[-1] += parts[-1]
            else:
                sentences.append(parts[-1])
        
        return sentences
    
    def _split_long_sentence(self, sentence: str) -> List[str]:
        """拆分超长句子"""
        if self._is_english(sentence):
            words = sentence.split()
            return self._merge_by_words(words)
        
        words = self._simple_chinese_split(sentence)
        return self._merge_by_words(words, use_chinese=True)
    
    def _is_english(self, text: str) -> bool:
        """判断是否为纯英文文本"""
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        return chinese_chars == 0 and len(text) > 0
    
    def _simple_chinese_split(self, text: str) -> List[str]:
        """简单中文分词（不依赖jieba）"""
        words = []
        current_word = ""
        
        for char in text:
            if re.match(r'[\u4e00-\u9fff]', char):
                if current_word:
                    words.append(current_word)
                    current_word = ""
                words.append(char)
            elif char.isspace():
                if current_word:
                    words.append(current_word)
                    current_word = ""
            else:
                current_word += char
        
        if current_word:
            words.append(current_word)
        
        return [w for w in words if w.strip()]
    
    def _merge_by_words(self, words: List[str], use_chinese: bool = False) -> List[str]:
        """将词列表合并为片段"""
        chunks = []
        current_chunk = ""
        
        for word in words:
            word = word.strip()
            if not word:
                continue
            
            test_chunk = current_chunk + (" " if current_chunk else "") + word
            
            if len(test_chunk) <= self.max_length:
                current_chunk = test_chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                
                if len(word) > self.max_length:
                    word_chunks = self._force_split(word)
                    chunks.extend(word_chunks[:-1])
                    current_chunk = word_chunks[-1] if word_chunks else ""
                else:
                    current_chunk = word
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _force_split(self, text: str) -> List[str]:
        """强制拆分超长文本"""
        chunks = []
        for i in range(0, len(text), self.max_length):
            chunk = text[i:i + self.max_length]
            if chunk:
                chunks.append(chunk)
        return chunks
    
    def _merge_short_chunks(self, chunks: List[str]) -> List[str]:
        """合并过短的片段"""
        if not chunks:
            return chunks
        
        merged = [chunks[0]]
        
        for chunk in chunks[1:]:
            if len(merged[-1]) + len(chunk) + 1 <= self.max_length:
                merged[-1] = merged[-1] + " " + chunk
            elif len(chunk) < self.min_chunk_length and len(merged[-1]) + len(chunk) + 1 <= self.max_length:
                merged[-1] = merged[-1] + " " + chunk
            else:
                merged.append(chunk)
        
        return merged


def split_text(text: str, max_length: int = 200, **kwargs) -> SplitResult:
    """拆分文本的便捷函数"""
    splitter = TextSplitter(max_length=max_length, **kwargs)
    return splitter.split(text)
