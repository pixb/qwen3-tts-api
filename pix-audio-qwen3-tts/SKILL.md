---
name: pix-audio-qwen3-tts
description: This skill should be used when the user asks to convert text to speech, generate audio, create TTS voice, or do voice synthesis. Activates with phrases like 语音合成, TTS, 文字转语音, 生成语音, 配音, 朗读. Provides text formatting, text splitting, TTS generation, and audio merging workflow.
---

# pix-audio-qwen3-tts

## 基础信息

| 属性 | 值 |
| :--- | :--- |
| **名称** | pix-audio-qwen3-tts |
| **版本** | 1.0.0 |
| **类型** | 简单技能 |
| **核心功能** | 将文本转换为语音，包括文本格式化、分片、生成、合并的完整工作流 |
| **适用环境** | Trae / opencode |

## 核心目标

将非标准化的书面文本转换为适合 TTS 模型朗读的口语脚本，并通过 Qwen3-TTS MCP 生成自然流畅的语音输出。

## 使用方法

### 激活方式

当用户请求以下内容时，skill 会自动激活：

- 语音合成、TTS、文字转语音
- 生成语音、配音、朗读
- 将文本转为音频、把文字读出来

### 执行步骤 (TODO List)

当 AI 执行任务时，按以下步骤进行，并在每步完成后向用户汇报进度：

- [ ] 1. **文本格式化** - 调用 `format_tts_text()` 格式化输入文本
- [ ] 2. **文本分片** - 调用 `text_split()` 拆分成长度 ≤100 字符的片段
- [ ] 3. **语音生成** - 循环调用 `tts_generate()` 生成每个片段
- [ ] 4. **音频合并** - 调用 `audio_merge()` 合并所有片段
- [ ] 5. **返回结果** - 返回下载链接或文件路径

### 工作流程

```
1. 文本格式化 → 2. 文本分片 → 3. 语音生成 → 4. 音频合并 → 5. 返回结果
```

## 功能说明

### 1. 文本格式化 (format_tts_text)

将书面文本转换为口语化表达：

| 规则 | 示例 | 处理结果 |
|------|------|----------|
| 数字+单位 | `2022 年`, `100 %` | `2022年`, `100%` |
| 日期格式 | `2023-10-01` | `2023年10月1日` |
| 时间格式 | `12:30` | `12点30分` |
| 特殊符号 | `&`, `@`, `#` | `和`, `在`, 去除 |
| Markdown | `**加粗**`, `## 标题` | 去除符号 |
| URL | `https://...` | 去除 |
| 多音字 | `行长` | `银行行长` |

### 2. 文本分片 (text_split)

将长文本拆分为适合 TTS 处理的短片段，智能断句。

### 3. 语音生成 (tts_generate)

使用参考音频生成语音，支持参数覆盖。

### 4. 音频合并 (audio_merge)

将多个音频片段合并为一个完整音频。

## MCP 工具

| 工具名 | 功能 | 耗时操作 |
|--------|------|----------|
| `text_split` | 文本分片 | - |
| `reference_list` | 列出参考音频 | - |
| `tts_generate` | 语音生成 | ✓ |
| `audio_merge` | 音频合并 | - |

## 工作流封装

### text_to_speech()

```python
async def text_to_speech(
    text: str,
    reference_name: str = "tianyuan",
    output_dir: str = "output",
    language: str = "Auto",
    exaggeration: float = None,
    temperature: float = None,
    speed_rate: float = None,
    instruct: str = None,
    max_length: int = 100,
) -> dict:
    """将文本转换为语音的完整工作流"""
    # 1. 文本格式化
    formatted_text = format_tts_text(text)
    
    # 2. 文本分片
    split_result = await text_split(formatted_text, max_length=max_length)
    chunks = split_result.get("chunks", [])
    
    if not chunks:
        return {"success": False, "error": "文本分片失败"}
    
    # 3. 语音生成
    audio_files = []
    for i, chunk in enumerate(chunks):
        result = await tts_generate(
            text=chunk,
            reference_name=reference_name,
            ref_text="",  # 会自动从参考音频获取默认值
            language=language,
            exaggeration=exaggeration,
            temperature=temperature,
            speed_rate=speed_rate,
            output_dir=output_dir,
        )
        if result.get("success"):
            audio_files.append(result["file_path"])
    
    if not audio_files:
        return {"success": False, "error": "语音生成失败"}
    
    # 4. 音频合并
    merged = await audio_merge(files=audio_files, output_dir=output_dir)
    
    return merged
```

### format_tts_text()

```python
def format_tts_text(text: str) -> str:
    """格式化文本为适合 TTS 朗读的口语化脚本"""
    import re
    
    # 1. 数字与单位连接
    text = re.sub(r'(\d+)\s*([年日月时分秒公斤千克克米厘米毫米%])', r'\1\2', text)
    text = re.sub(r'(\d+)\s*([0-9]+)', r'\1\2', text)
    
    # 2. 日期与时间标准化
    text = re.sub(r'(\d{4})-(\d{1,2})-(\d{1,2})', r'\1年\2月\3日', text)
    text = re.sub(r'(\d{1,2}):(\d{2})', r'\1点\2分', text)
    
    # 3. 特殊符号处理
    text = text.replace('&', '和').replace('@', '在')
    text = re.sub(r'[#*~]', '', text)
    
    # 4. 去除 Markdown 格式
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'#+\s*', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    
    # 5. 去除 URL
    text = re.sub(r'https?://[^\s]+', '', text)
    
    # 6. 去除注脚
    text = re.sub(r'\[\d+\]', '', text)
    text = re.sub(r'\(注[：:]?[^)]*\)', '', text)
    
    return text.strip()
```

## 使用示例

### 示例 1: 简单文本转语音

```
用户: "将这段文字生成语音：今天天气真好，适合出去散步。"

AI 执行步骤:
- [x] 1. 文本格式化 → "今天天气真好，适合出去散步。"
- [x] 2. 文本分片 → ["今天天气真好，适合出去散步。"]
- [x] 3. 语音生成 → "output/tts_123.wav"
- [x] 4. 音频合并 → (单片段跳过合并)
- [x] 5. 返回结果 → "语音已生成: http://localhost:8001/audio/tts_123.wav"
```

### 示例 2: 长文本转语音

```
用户: "将这篇文档生成语音并保存到 /tmp/audio 目录"

AI 执行步骤:
- [x] 1. 文本格式化 → 格式化后的文本
- [x] 2. 文本分片 → ["片段1", "片段2", "片段3"] (3个片段)
- [x] 3. 语音生成 → output/1.wav, 2.wav, 3.wav
- [x] 4. 音频合并 → "/tmp/audio/merged.wav"
- [x] 5. 返回结果 → "语音已保存到 /tmp/audio/merged.wav"
```

### 示例 3: 自定义语音参数

```
用户: "用更快更活泼的语音风格生成这段文字"

AI 执行步骤:
- [x] 1. 文本格式化
- [x] 2. 文本分片
- [x] 3. 语音生成 (exaggeration=0.8, speed_rate=1.2)
- [x] 4. 音频合并
- [x] 5. 返回结果
```

## 最佳实践

1. **参考音频选择**: 使用 `reference_list` 先查看可用的参考音频，选择最符合场景的
2. **文本长度控制**: 长文本默认 `max_length=100`，可按需调整
3. **参数调优**:
   - `exaggeration`: 情感夸张程度，值越大情感越丰富
   - `temperature`: 采样温度，值越大随机性越高
   - `speed_rate`: 语速，0.5~2.0 之间
   - `instruct`: 语音风格指令，描述期望的朗读风格
4. **批量处理**: 大量文本可分批处理，避免超时
5. **错误处理**: 始终检查每步的 `success` 字段，确保流程正常

## 注意事项

- 需要先启动 TTS 服务：`python -m uvicorn src.qwen3_tts_api.main:app --port 8001`
- 需要配置 MCP Server 到 opencode
- `tts_generate` 为耗时操作，MCP 超时设置为 20 分钟
- 生成的音频保存在 output 目录，可通过 `/audio/{filename}` 访问
